from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_staff_group(apps, schema_editor):
    group, created = Group.objects.get_or_create(name="Admin")

    book_ct, _ = ContentType.objects.get_or_create(app_label="file_upload", model="book")
    transcription_ct, _ = ContentType.objects.get_or_create(
        app_label="file_upload", model="transcription"
    )
    revision_ct, _ = ContentType.objects.get_or_create(app_label="file_upload", model="revision")

    permissions = Permission.objects.filter(
        content_type__in=[book_ct, transcription_ct, revision_ct]
    )

    group.permissions.set(permissions)


def reverse_staff_group(apps, schema_editor):
    Group.objects.filter(name="Admin").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("file_upload", "0002_alter_revision_index"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(create_staff_group, reverse_staff_group),
    ]