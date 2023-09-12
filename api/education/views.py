import json

from django.http import JsonResponse

from clients.models import Citizenship
from education.models import ApplicationEducation, ExamType, Subjects, AchievementType, DocumentTypeEducation, SpecialRights, EducationSpeciality, Achievement, EducationFinanceSource
from education.views import get_all_enrollees
from laboratory.local_settings import SUBJECTS_ENTRANCE_EXAM
from laboratory.utils import current_year


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


def get_pay_forms(request):
    result = EducationFinanceSource.get_sources()
    return JsonResponse({"result": result})


def get_citizenship(request):
    result = Citizenship.get_citizenship()
    return JsonResponse({"result": result})


def get_exams_filters(request):
    exam_types = ExamType.get_types()
    subjects = Subjects.get_subjects()
    return JsonResponse({"exam_types": exam_types, "subjects": subjects})


def get_achievements_filters(request):
    achievements = AchievementType.get_types()
    return JsonResponse({"achievements": achievements})


def get_education(request):
    result = DocumentTypeEducation.get_education_documents_tree()
    return JsonResponse({"result": result})


def get_special_rights(request):
    result = SpecialRights.get_special_rights_tree()
    return JsonResponse({"result": result})


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
        {"field": 'is_original', "key": 'is_original', "title": 'Оригинал'},
        {"field": 'researchContractId', "key": 'researchContractId', "title": 'Договор'},
        {"field": 'status', "key": 'status', "title": 'Статус'},
        {"field": 'create_date', "key": 'create_date', "title": 'Создано'},
    ]
    step = 0
    for i in entrance_exam_data:
        columns.insert(4 + step, {"field": i.synonym, "key": i.synonym, "title": i.short_title})
        step += 1

    return JsonResponse({"result": columns})


def get_enrollees(request):
    data = get_all_enrollees(request)
    return JsonResponse({"data": data})


def get_applications_by_card(request):
    request_data = json.loads(request.body)
    result = ApplicationEducation.get_applications_by_card(request_data["card_pk"])
    return JsonResponse({"result": result})


def get_achievement_by_card(request):
    request_data = json.loads(request.body)
    result = Achievement.get_achievement_by_card(request_data["card_pk"])
    return JsonResponse({"result": result})
