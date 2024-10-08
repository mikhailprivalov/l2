from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import simplejson as json

from api.statement.sql import get_tubes_without_statement, get_who_create_directions, get_directions_by_tube_regitration_number, get_statement_document_data
from directions.models import Napravleniya, StatementDocument, TubesRegistration
from utils.dates import normalize_dots_date
from django.db import transaction


@login_required
def select_tubes_statement(request):
    data = json.loads(request.body)
    user = request.user.doctorprofile.pk
    data_start = normalize_dots_date(data.get('date_from'))
    data_start = f"{data_start} 00:00:01"
    data_end = normalize_dots_date(data.get('date_to'))
    data_end = f"{data_end} 23:59:59"
    directions = list(Napravleniya.objects.filter(data_sozdaniya__gte=data_start, data_sozdaniya__lte=data_end).values_list("pk", flat=True))
    sql_data = get_tubes_without_statement(tuple(directions), user)

    result = [
        {
            "fio": f"{i.patient_family} {i.patient_name} {i.patient_patronymic}- {i.patient_birthday} ({i.card_number})",
            "direction": i.direction_id,
            "tubeNumber": i.tube_number,
            "checked": False
        } for i in sql_data
    ]

    return JsonResponse({"rows": result})


@login_required
def save_tubes_statement(request):
    data = json.loads(request.body)
    user_id = request.user.doctorprofile.pk
    directions = [d.get('direction') for d in data]
    tube_numbers = [d.get('tubeNumber') for d in data]
    result = True
    message = ""

    sql_who_create = get_who_create_directions(tuple(directions))
    if (len(sql_who_create) > 1) or sql_who_create[0].doc_who_create_id != user_id:
        result = False
        message = "Ошибка в доступе пользователя"
    else:
        sql_tubes_data = get_directions_by_tube_regitration_number(tuple(tube_numbers))
        directions_by_tube = list(set([i.direction_id for i in sql_tubes_data]))
        if sorted(directions_by_tube) != sorted(directions):
            result = False
            message = "Ошибка в кол-ве направления"

    if result:
        with transaction.atomic():
            statement_document = StatementDocument(person_who_create_id=user_id)
            statement_document.save()
            tubes = TubesRegistration.objects.filter(number__in=tube_numbers)
            for t in tubes:
                t.statement_document = statement_document
                t.save()

    return JsonResponse({"ok": result, "message": message})


@login_required
def show_history(request):
    user_id = request.user.doctorprofile.pk
    statement_document =list(StatementDocument.objects.filter(person_who_create_id=user_id).values_list("pk", flat=True))
    sql_statemnt = get_statement_document_data(tuple(statement_document))

    result = [
        {
            "date": i.date_create,
            "direction": i.direction_id,
            "tubeNumber": i.tube_number,
            "checked": False
        } for i in sql_statemnt
    ]

    return JsonResponse({"rows": result})



