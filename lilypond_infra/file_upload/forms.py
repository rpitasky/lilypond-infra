from django import forms

from .models import Revision, get_latest_template_version


class RevisionForm(forms.ModelForm):
    template_tag = forms.CharField(
        required=False,
        help_text="Git tag to checkout when rendering. (defaults to latest)",
    )

    class Meta:
        model = Revision
        fields = ["lilypond_source", "template_tag"]

    def clean_template_tag(self):
        return self.cleaned_data.get("template_tag") or get_latest_template_version()
