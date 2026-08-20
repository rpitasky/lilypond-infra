from django.contrib import admin
from django.db.models import QuerySet
from django.urls import reverse

from file_upload.models import Transcription, Book, Revision, Config


# Register your models here.
@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    filter_horizontal = ("transcriptions",)

    def view_on_site(self, obj):
        return reverse("book_detail", args=[obj.id])


class RevisionInline(admin.TabularInline):
    model = Revision

    extra = 1
    autocomplete_fields = ("creator",)


@admin.action(description="Rerender Latest PDFs")
def rerender_pdfs(modeladmin, request, queryset: QuerySet):
    for transcription in queryset.all():
        revision = transcription.latest_revision()
        revision.render_pdf()


@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    inlines = [RevisionInline]
    actions = [rerender_pdfs]

    def view_on_site(self, obj):
        return reverse("transcription_detail", args=[obj.id])
