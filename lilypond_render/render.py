# I hoped to vibecode this (shh) but the result was fucking awful so i just did it myself

# setup: checkout tag in local repo, copy files to tempdir
# tempdir structure:
# - /lilypond-jobs/job/{uuid4}
#   - raw-template/ {git repository}
#   - transcription.ly
#   - out/
import asyncio
import os
import shlex
import shutil
import subprocess
import tempfile
import uuid
import warnings
import zipfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

api = FastAPI(title="LilyPond Render Service")
SCRIPT_DIR = Path(__file__).parent

REPO_PATH = Path(SCRIPT_DIR / "raw-template").resolve()
if not REPO_PATH.is_dir():
    raise RuntimeError("raw-template not found")
JOBS_ROOT = Path(tempfile.gettempdir()) / "lilypond-jobs"
JOBS_ROOT.mkdir(exist_ok=True)

MAX_TIMEOUT = 120
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

BUBBLEWRAP = shutil.which("bwrap")
if not BUBBLEWRAP:
    warnings.warn("bwrap not found, sandboxing will be disabled")
LILYPOND = shutil.which("lilypond") or os.environ.get("LILYPOND_PATH")
if not LILYPOND:
    raise RuntimeError("lilypond not found")
else:
    print(f"Using lilypond at {LILYPOND}")


@api.get("/health")
async def health():
    return {"status": "ok" if BUBBLEWRAP else "ok, sandboxing disabled"}


@api.get("/git-pull")
async def git_pull():
    proc = await asyncio.create_subprocess_exec(
        "git", "-C", str(REPO_PATH), "pull", "origin", "main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise HTTPException(500, f"git pull failed: {stderr.decode(errors='replace').strip()}")

    return {"status": "ok"}


@api.get("/git-tags")
async def git_tags():
    proc = await asyncio.create_subprocess_exec(
        "git", "-C", str(REPO_PATH), "tag", "-l", "--sort=-v:refname",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise HTTPException(500, f"git pull failed: {stderr.decode(errors='replace').strip()}")
    return {"tags": stdout.decode(errors="replace").strip().split("\n")}


@api.post("/render")
async def render(
    file: UploadFile = File(...),
    tag: str = Form(...),
    options: str = Form(""),
    timeout: int = Form(30),
):
    job_id = uuid.uuid4().hex
    timeout = min(max(int(timeout), 1), MAX_TIMEOUT)

    contents = await file.read()

    job_dir = setup_job_directory(job_id, contents, tag)

    out_dir = job_dir / "out"
    out_dir.mkdir(exist_ok=True)

    lilypond_args = [
        "-o", "out",
        *shlex.split(options),
        str(job_dir / "transcription.ly"),
    ]

    if not BUBBLEWRAP:
        await lilypond_unsandboxed(lilypond_args, job_dir, timeout)
    else:
        await lilypond_sandboxed(job_dir / "transcription.ly", job_dir / "template", out_dir, lilypond_args, timeout)

    result = process_output(job_dir, out_dir)

    response = FileResponse(path=result, filename=result.name)
    response.background = BackgroundTask(lambda: shutil.rmtree(job_dir, ignore_errors=True))
    return response


async def lilypond_unsandboxed(args: list[str], job_dir: Path, timeout: float):
    proc = await asyncio.create_subprocess_exec(
        *[LILYPOND, *args],
        cwd=job_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(504, f"render timed out after {timeout}s")

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")[-4000:]
        raise HTTPException(422, err)

def process_output(job_dir: Path, out_dir: Path) -> Path:
    outputs = sorted(p for p in out_dir.iterdir() if p.is_file())
    if not outputs:
        raise HTTPException(500, "lilypond exited 0 but produced no output files")

    if len(outputs) == 1:
        result_path = outputs[0]
    else:
        result_path = job_dir / "output.zip"
        with zipfile.ZipFile(result_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in outputs:
                zf.write(p, arcname=p.name)

    return result_path

def checkout(git_tag: str):
    verify_tag = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{git_tag}"],
        cwd=REPO_PATH,
        capture_output=True,
        text=True,
    )

    if verify_tag.returncode != 0:
        raise HTTPException(400, f"Tag '{git_tag}' does not exist in this repository.")

    subprocess.run(
        ["git", "checkout", git_tag],
        cwd=REPO_PATH,
        capture_output=True,
        text=True,
        check=True,
    )


def copy_template_repo(out_dir: Path, git_tag: str):
    checkout(git_tag)

    shutil.copytree(REPO_PATH, out_dir, dirs_exist_ok=True)


def setup_job_directory(job_id: str, file: bytes, git_tag: str) -> Path:
    job_dir = JOBS_ROOT / job_id
    job_dir.mkdir(parents=True)
    ly_file = job_dir / "transcription.ly"
    ly_file.write_bytes(file)


    copy_template_repo(job_dir / "raw-template", git_tag)

    return job_dir


async def lilypond_sandboxed(input_path: Path, template_dir: Path, out_dir: Path, lilypond_args: list[str], timeout: int):
    bwrap_cmd = [
        "bwrap",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind-try", "/lib64", "/lib64",
        "--ro-bind", "/etc/fonts", "/etc/fonts",
        "--ro-bind", "/usr/share/fonts", "/usr/share/fonts",
        "--ro-bind-try", "/var/cache/fontconfig", "/var/cache/fontconfig",
        "--ro-bind", str(template_dir), "/job/template",
        "--ro-bind", str(input_path), f"/job/{input_path.name}",
        "--bind", str(out_dir), "/job/out",
        "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "HOME", "/tmp",
        "--proc", "/proc",
        "--dev", "/dev",
        "--unshare-net",
        "--unshare-pid",
        "--die-with-parent",
        "--chdir", "/job",
        LILYPOND,
        *lilypond_args,
    ]

    proc = await asyncio.create_subprocess_exec(
        *bwrap_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(504, f"render timed out after {timeout}s")

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")[-4000:]
        raise HTTPException(422, err)

async def start_api():
    config = uvicorn.Config(api, host='127.0.0.1', port=8002, log_level='error')
    server = uvicorn.Server(config)
    print('Starting API server on port 8002')
    await server.serve()

if __name__ == '__main__':
    asyncio.run(start_api())