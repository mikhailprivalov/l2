from hospitals.models import Hospitals


def check_correct_hosp(request, oid_org):
    if not oid_org:
        return {"OK": False, "message": 'Должно быть указано org.oid'}

    hospital = Hospitals.objects.filter(oid=oid_org).first()
    if not hospital:
        return {"OK": False, "message": 'Организация не найдена'}

    if not request.user.hospitals.filter(pk=hospital.pk).exists():
        return {"OK": False, "message": 'Нет доступа в переданную организацию'}

    return {"OK": True, "hospital": hospital}
