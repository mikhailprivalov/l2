from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.utils.http import urlquote


def group_required(*group_names):
    def in_group(u):
        if "admin" in group_names:
            return u.is_active and u.is_superuser
        return u.is_active and (u.is_superuser or bool(u.groups.filter(name__in=group_names)))

    return user_passes_test(in_group)


def logged_in_or_token(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        if request.GET.get('token', request.POST.get('token')) == "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7":
            return view_func(request, *args, **kwargs)
        return HttpResponseRedirect('/?next=' + urlquote(request.get_full_path()))
    return _wrapped_view
