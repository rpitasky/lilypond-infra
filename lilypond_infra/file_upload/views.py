import io
import zipfile
from hashlib import sha256

from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from extern.discord_bot import discord_role_required, user_has_role
import discord_settings
from .forms import RevisionForm
from .models import Book, Revision, Transcription


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    transcriptions = book.transcriptions.all()
    return render(
        request,
        "book_detail.html",
        {
            "user": request.user,
            "book": book,
            "transcriptions": transcriptions,
        },
    )


def _book_download_zip(request, book_id, file_field, extension):
    book = get_object_or_404(Book, pk=book_id)

    checksum_data = []
    excluded_files = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for transcription in book.transcriptions.order_by("id").all():
            revision = transcription.latest_revision()

            if revision is None:
                checksum_data.append((transcription.title, None))
                excluded_files.append(
                    f"{transcription.title} (no transcription available)"
                )
                continue

            checksum_data.append((transcription.title, revision.index))

            file_obj = getattr(revision, file_field)
            if not file_obj:
                excluded_files.append(
                    f"{transcription.title} (no {extension.upper()} available)"
                )
                continue

            with file_obj.open("rb") as f:
                zf.writestr(f"{transcription.id}.{extension}", f.read())

        if excluded_files:
            zf.writestr("excluded_files.txt", "\n".join(excluded_files))

    checksum = sha256(repr(checksum_data).encode("utf-8")).hexdigest()[:6]

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = (
        f'attachment; filename="{book.id}-{extension}-{checksum}.zip"'
    )
    return response


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def book_download_ly_zip(request, book_id):
    return _book_download_zip(request, book_id, "lilypond_source", "ly")


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def book_download_pdf_zip(request, book_id):
    return _book_download_zip(request, book_id, "pdf_file", "pdf")


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def transcription_detail(request, transcription_id):
    transcription = get_object_or_404(Transcription, pk=transcription_id)
    revisions = transcription.revisions.select_related("creator").order_by("-index")
    books = transcription.books.values("id", "title")

    can_upload_revisions = user_has_role(
        request.user, discord_settings.LILYPOND_ROLE_ID
    )

    if request.method == "POST":
        if not can_upload_revisions:
            return PermissionDenied("You don't have permission to upload revisions.")

        form = RevisionForm(request.POST, request.FILES)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.transcription = transcription
            revision.creator = request.user
            revision.save()
            revision.render_pdf()
            return redirect("transcription_detail", transcription_id=transcription.id)
    else:
        form = RevisionForm()

    return render(
        request,
        "transcription_detail.html",
        {
            "transcription": transcription,
            "books": books,
            "revisions": revisions,
            "form": form,
            "can_upload_revisions": can_upload_revisions,
        },
    )


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def revision_download_ly(request, transcription_id, index):
    revision = get_object_or_404(
        Revision, transcription_id=transcription_id, index=index
    )
    if not revision.lilypond_source:
        raise Http404("No file for this revision")

    return FileResponse(
        revision.lilypond_source.open("rb"),
        content_type="text/plain; charset=utf-8",
        as_attachment=False,
        filename=f"{revision.transcription.id}_r{revision.index}.ly",
    )


@discord_role_required(discord_settings.LILYPOND_ROLE_ID)
def revision_download_pdf(request, transcription_id, index):
    revision = get_object_or_404(
        Revision, transcription_id=transcription_id, index=index
    )
    if not revision.pdf_file:
        raise Http404("No file for this revision")

    return FileResponse(
        revision.pdf_file.open("rb"),
        content_type="application/pdf",
        as_attachment=False,
        filename=f"{revision.transcription.id}_r{revision.index}.pdf",
    )


@discord_role_required(discord_settings.COLLABORATOR_ROLE_ID)
def book_list(request):
    books = Book.objects.all()
    return render(request, "book_list.html", {"books": books})


def home(request):
    if request.user.is_authenticated:
        return redirect("book_list")
    else:
        return redirect("accounts/login")
