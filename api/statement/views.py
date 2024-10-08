from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def select_tubes_statemen(request):
    pass
    return JsonResponse({"results": ""})


@login_required
def select_tubes_statement(request):
    pass
    return JsonResponse({"results": ""})
