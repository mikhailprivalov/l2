import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clients.models import Citizenship
from education.models import ApplicationEducation, ExamType, Subjects, AchievementType, DocumentTypeEducation, SpecialRights, EducationSpeciality, Achievement, EducationFinanceSource
from education.views import get_all_enrollees
from laboratory.decorators import group_required
from laboratory.local_settings import SUBJECTS_ENTRANCE_EXAM
from laboratory.utils import current_year


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_specialties(request):
    request_data = json.loads(request.body)
    year_start_study = request_data.get('yearStartStudy')
    if not year_start_study:
        year_start_study = current_year()
    else:
        year_start_study = year_start_study.get('value')
        year_start_study = year_start_study.get('label')

    result = EducationSpeciality.get_speciality(year_start_study)
    return JsonResponse({"result": result})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_pay_forms(request):
    result = EducationFinanceSource.get_sources()
    return JsonResponse({"result": result})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_citizenship(request):
    result = Citizenship.get_citizenship()
    return JsonResponse({"result": result})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_exams_filters(request):
    exam_types = ExamType.get_types()
    subjects = Subjects.get_subjects()
    return JsonResponse({"exam_types": exam_types, "subjects": subjects})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_achievements_filters(request):
    achievements = AchievementType.get_types()
    return JsonResponse({"achievements": achievements})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_education(request):
    result = DocumentTypeEducation.get_education_documents_tree()
    return JsonResponse({"result": result})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_special_rights(request):
    result = SpecialRights.get_special_rights_tree()
    return JsonResponse({"result": result})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_columns(request):
    entrance_exam_data = Subjects.objects.filter(pk__in=SUBJECTS_ENTRANCE_EXAM)

    columns = [
        {"field": 'card', "key": 'card', "title": 'Дело'},
        {"field": 'fio', "key": 'fio', "title": 'ФИО'},
        {"field": 'applicationSpeciality', "key": 'applicationSpeciality', "title": 'Специальность'},
        {"field": 'applicationPersonNumber', "key": 'applicationPersonNumber', "title": 'Номер'},
        {"field": 'achievementPoint', "key": 'achievementPoint', "title": 'ИД'},
        {"field": 'achievementСhecked', "key": 'achievementСhecked', "title": 'ИД+'},
        {"field": 'totalPoints', "key": 'totalPoint', "title": 'Сумм'},
        {"field": 'isOriginal', "key": 'isOriginal', "title": 'Оригинал'},
        {"field": 'researchContractId', "key": 'researchContractId', "title": 'Договор'},
        {"field": 'status', "key": 'status', "title": 'Статус'},
        {"field": 'createDate', "key": 'create_date', "title": 'Создано'},
    ]
    for i in entrance_exam_data:
        columns.insert(4, {"field": i.synonym, "key": i.synonym, "title": i.short_title})

    return JsonResponse({"result": columns})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_enrollees(request):
    data = get_all_enrollees(request)
    return JsonResponse({"data": data})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_applications_by_card(request):
    request_data = json.loads(request.body)
    applications, columns = ApplicationEducation.get_applications_by_card(request_data["card_pk"])
    return JsonResponse({"applications": applications, "columns": columns})


@login_required
@group_required('Приемная комиссия: Абитуриенты')
def get_achievement_by_card(request):
    request_data = json.loads(request.body)
    achievements = Achievement.get_achievement_by_card(request_data["card_pk"])
    return JsonResponse({"achievements": achievements})
