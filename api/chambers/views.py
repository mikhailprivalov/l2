from podrazdeleniya.models import Chamber

import simplejson as json
from django.http import JsonResponse


def all_chambers(request):
    req = json.loads(request.body)
    current_user_hospital_id = request.user.doctorprofile.get_hospital_id()
    su = request.user.is_superuser or request.user.doctorprofile.all_hospitals_users_control
    can_edit = su or request.user.doctorprofile.has_group('Управление палатами')

    if can_edit:
        chambers = [{"label": chamber.title, "pk": chamber.id} for chamber in Chamber.objects.filter(hospital_id=current_user_hospital_id).order_by('title', 'id')]
        print(chambers)
        return JsonResponse({"data": chambers})
    return JsonResponse(0)
