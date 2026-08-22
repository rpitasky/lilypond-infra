from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple, RelatedFieldWidgetWrapper
from django.db.models import QuerySet
from django.db.models.aggregates import Max
from django.urls import reverse
from django.utils.safestring import mark_safe

from file_upload.models import Transcription, Book, Revision, Config, BookContents


# Register your models here.
@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")


class BookAdminForm(forms.ModelForm):
    transcriptions = forms.ModelMultipleChoiceField(
        queryset=Transcription.objects.all(),
        required=False,
        widget=RelatedFieldWidgetWrapper(
            FilteredSelectMultiple("transcriptions", is_stacked=False),
            Book.transcriptions.rel,
            admin.site,
            can_add_related=True,
            can_change_related=False,
            can_delete_related=False,
            can_view_related=False,
        ),
    )
    class Meta:
        model = Book
        fields = ("title",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["transcriptions"].initial = self.instance.transcriptions.all()


class BookContentsInlineForm(forms.ModelForm):
    class Meta:
        model = BookContents
        fields = ("transcription", "revision", "order")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["revision"].help_text = (
            "By default, the latest revision is used in book exports. Pin a specific revision to stop tracking transcription updates."
        )
        if self.instance and self.instance.transcription_id:
            self.fields["revision"].queryset = Revision.objects.filter(
                transcription_id=self.instance.transcription_id
            ).order_by("-index")
        else:
            self.fields["revision"].queryset = Revision.objects.none()


class BookContentsOrderInline(SortableInlineAdminMixin, admin.TabularInline):
    model = BookContents
    form = BookContentsInlineForm
    extra = 0
    fields = ("transcription", "revision", "order")
    readonly_fields = ("transcription",)
    ordering = ("order",)
    verbose_name_plural = "Reorder transcriptions"

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {"all": ("admin/css/sortable-tabular-inline-fixes.css",)}


@admin.register(Book)
class BookAdmin(SortableAdminBase, admin.ModelAdmin):
    form = BookAdminForm
    list_display = ("title",)
    search_fields = ("title",)
    inlines = [BookContentsOrderInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        selected = set(form.cleaned_data["transcriptions"].values_list("id", flat=True))
        existing = set(obj.bookcontents_set.values_list("transcription_id", flat=True))

        to_add = selected - existing
        to_remove = existing - selected

        if to_remove:
            obj.bookcontents_set.filter(transcription_id__in=to_remove).delete()

        if to_add:
            next_order = (obj.bookcontents_set.aggregate(m=Max("order"))["m"] or 0) + 1
            BookContents.objects.bulk_create(
                BookContents(book=obj, transcription_id=t_id, order=next_order + i)
                for i, t_id in enumerate(to_add)
            )

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

    search_fields = ("title",)

    def view_on_site(self, obj):
        return reverse("transcription_detail", args=[obj.id])

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)
