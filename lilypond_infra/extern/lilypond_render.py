import io
import os
from pathlib import Path

import requests

LILYPOND_RENDER_API = os.environ.get("RENDER_SERVICE_URL", "http://127.0.0.1:8002")


def git_pull():
    resp = requests.get(f"{LILYPOND_RENDER_API}/git-pull", timeout=30)
    resp.raise_for_status()
    return resp.json()


def git_tags() -> list[str]:
    resp = requests.get(f"{LILYPOND_RENDER_API}/git-tags", timeout=10)
    resp.raise_for_status()
    return resp.json()["tags"]


def render(
    ly_path: str | Path,
    tag: str,
    options: str = "",
    timeout: int = 30,
) -> io.BytesIO:
    ly_path = Path(ly_path)
    if not ly_path.is_file():
        raise FileNotFoundError(ly_path)

    with ly_path.open("rb") as f:
        files = {"file": (ly_path.name, f, "application/octet-stream")}
        data = {"tag": tag, "options": options, "timeout": str(timeout)}

        resp = requests.post(
            f"{LILYPOND_RENDER_API}/render",
            files=files,
            data=data,
            timeout=timeout + 10,
        )

    if not resp.ok:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise RuntimeError(f"Render failed [{resp.status_code}]: {detail}")

    file_obj = io.BytesIO(resp.content)
    file_obj.name = _filename_from_response(resp) or "output"
    file_obj.seek(0)
    return file_obj


def _filename_from_response(resp: requests.Response) -> str | None:
    cd = resp.headers.get("content-disposition", "")
    if "filename=" in cd:
        return cd.split("filename=", 1)[1].strip('"; ')
    return None
