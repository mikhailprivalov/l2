from django.contrib.auth.models import Group


def has_group(user, *group_names, force_superuser=False):
    if force_superuser and user.is_superuser:
        return True
    for group_name in group_names:
        group = Group.objects.filter(name=group_name).first()
        if group and group in user.groups.all():
            return True
    return False
