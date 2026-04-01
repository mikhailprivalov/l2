from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from urllib.parse import quote

from laboratory.settings import USE_COMBO_ROLE


def group_required(*group_names):
    def in_group(u):
        if "admin" in group_names:
            return u.is_active and u.is_superuser

        groups_user = [str(x) for x in u.groups.all()]
        detail_user_group = []
        for i in groups_user:
            if USE_COMBO_ROLE.get(i):
                detail_user_group.extend(USE_COMBO_ROLE.get(i))

        is_user_has_true_group = False
        for i in group_names:
            if i in detail_user_group:
                is_user_has_true_group = True
                break

        return u.is_active and (u.is_superuser or bool(u.groups.filter(name__in=group_names)) or is_user_has_true_group)

    return user_passes_test(in_group)


def logged_in_or_token(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        if request.GET.get('token', request.POST.get('token')) == "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7":
            return view_func(request, *args, **kwargs)
        return HttpResponseRedirect('/?next=' + quote(request.get_full_path()))

    return _wrapped_view
