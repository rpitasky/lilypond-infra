from django.urls import path

from . import views

urlpatterns = [
    path(r"book/", views.book_list, name="book_list"),
    path("book/<int:book_id>/", views.book_detail, name="book_detail"),
    path(
        "book/<int:book_id>/download/ly",
        views.book_download_ly_zip,
        name="book_download_ly_zip",
    ),
    path(
        "book/<int:book_id>/download/pdf",
        views.book_download_pdf_zip,
        name="book_download_pdf_zip",
    ),
    path(
        "transcription/<int:transcription_id>/",
        views.transcription_detail,
        name="transcription_detail",
    ),
    path(
        "transcription/<int:transcription_id>/revision<int:index>.ly",
        views.revision_download_ly,
        name="revision_download_ly",
    ),
    path(
        "transcription/<int:transcription_id>/revision<int:index>.pdf",
        views.revision_download_pdf,
        name="revision_download_pdf",
    ),
    path("", views.home, name="home"),
]
