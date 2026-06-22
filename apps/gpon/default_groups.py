from django.contrib.auth.models import Group, Permission


def create_groups(sender, **kwargs):
    g, _ = Group.objects.get_or_create(name="Доступ к GPON | readonly")
    g.permissions.add(
        *Permission.objects.filter(content_type__app_label="gpon", codename__contains="view"),
    )

    g, _ = Group.objects.get_or_create(name="Доступ к GPON | full access")
    g.permissions.add(
        *Permission.objects.filter(content_type__app_label="gpon"),
    )
