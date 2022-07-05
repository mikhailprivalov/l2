import directions.models as directions
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


def get_data_direction_with_param(direction_num):
    direction: directions.Napravleniya = directions.Napravleniya.objects.select_related('istochnik_f', 'client', 'client__individual', 'client__base').get(pk=direction_num)
    card = direction.client
    individual = card.individual
    iss = directions.Issledovaniya.objects.filter(
        napravleniye=direction,
    ).select_related('research')

    if not iss:
        return False

    services = [{"title": i.research.title, "code": i.research.code} for i in iss]

    direction_params_obj = directions.DirectionParamsResult.objects.filter(napravleniye_id=direction_num)
    direction_params = {dp.title: dp.value for dp in direction_params_obj}
    return {
        "pk": direction_num,
        "hosp": direction.hospital.title,
        "createdAt": direction.data_sozdaniya,
        "patient": {
            **card.get_data_individual(full_empty=True, only_json_serializable=True),
            "family": individual.family,
            "name": individual.name,
            "patronymic": individual.patronymic,
            "birthday": individual.birthday,
            "docs": card.get_n3_documents(),
            "sex": individual.sex,
        },
        "finSourceTitle": direction.istochnik_f.title if direction.istochnik_f else '',
        "priceCategory": direction.price_category.title if direction.price_category else '',
        "services": services,
        "directionParams": direction_params,
    }
