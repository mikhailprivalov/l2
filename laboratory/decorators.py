from django.contrib.auth.decorators import user_passes_test


def group_required(*group_names):
    def in_group(u):
        return u.is_active and (u.is_superuser or bool(u.groups.filter(name__in=group_names)))

    return user_passes_test(in_group)
