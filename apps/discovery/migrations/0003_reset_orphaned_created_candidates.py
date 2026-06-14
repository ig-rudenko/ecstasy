from django.db import migrations


def reset_orphaned_created_candidates(apps, schema_editor) -> None:
    """Вернуть осиротевших CREATED-кандидатов в статус READY."""

    discovery_candidate = apps.get_model("discovery", "DiscoveryCandidate")
    discovery_candidate.objects.filter(status="CREATED", device_id__isnull=True).update(status="READY")


class Migration(migrations.Migration):

    dependencies = [
        ("discovery", "0002_discoveryprofile_activate_created_devices"),
    ]

    operations = [
        migrations.RunPython(reset_orphaned_created_candidates, migrations.RunPython.noop),
    ]
