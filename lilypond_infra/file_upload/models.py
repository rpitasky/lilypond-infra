from django.core.files.base import ContentFile
from django.db import models, transaction
from django.conf import settings
from extern.lilypond_render import render


class Config(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.key


class Book(models.Model):
    id = models.CharField(primary_key=True, max_length=48)
    title = models.CharField(max_length=255)

    transcriptions = models.ManyToManyField(
        "Transcription",
        related_name="books",
    )

    def __str__(self):
        return self.title


class Transcription(models.Model):
    id = models.CharField(primary_key=True, max_length=48)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    def latest_revision(self):
        return self.revisions.order_by("-index").first()


def revision_lilypond_path(instance, filename):
    return f"lilypond/{instance.transcription.id}/revision{instance.index}.ly"


def revision_pdf_path(instance, filename):
    return f"pdf/{instance.transcription.id}/revision{instance.index}.pdf"


def get_latest_template_version():
    try:
        return Config.objects.values_list("value", flat=True).get(
            key="LATEST_TEMPLATE_VERSION"
        )
    except Config.DoesNotExist:
        return ""


class Revision(models.Model):
    index = models.PositiveIntegerField(editable=False)
    transcription = models.ForeignKey(
        Transcription, on_delete=models.CASCADE, related_name="revisions"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="revisions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    lilypond_source = models.FileField(upload_to=revision_lilypond_path)
    template_tag = models.CharField(
        max_length=255,
        help_text="Git tag from LilyPond template repository",
        default=get_latest_template_version,
    )

    pdf_file = models.FileField(upload_to=revision_pdf_path, null=True, blank=True)

    class Meta:
        ordering = ("index",)
        unique_together = ("transcription", "index")

    def __str__(self):
        return f"{self.transcription.title} - Revision {self.index}"

    def save(self, *args, **kwargs):
        if self._state.adding and self.index is None:
            with transaction.atomic():
                last_index = (
                    Revision.objects.select_for_update()
                    .filter(transcription=self.transcription)
                    .order_by("-index")
                    .values_list("index", flat=True)
                    .first()
                )
                self.index = (last_index or 0) + 1
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def render_pdf(self):
        result = render(self.lilypond_source.path, self.template_tag)

        if not result.name.endswith(".pdf"):
            raise ValueError("render() did not return a PDF")

        if self.pdf_file:
            self.pdf_file.delete(save=False)

        filename = revision_pdf_path(self, f"revision{self.index}.pdf")
        result.seek(0)
        self.pdf_file.save(filename, ContentFile(result.read()), save=True)
