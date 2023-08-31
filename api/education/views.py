import json

from django.http import JsonResponse

from clients.models import Citizenship
from directions.models import EducationFinanceSource
from education.models import ApplicationEducation, ExamType, Subjects, AchievementType, , DocumentTypeEducation, SpecialRights, EducationSpeciality
from education.views import get_all_enrollees


def get_specialties(request):
    result = EducationSpeciality.get_speciality()
    return JsonResponse({"result": result})


def get_pay_forms(request):
    result = EducationFinanceSource.get_sources()
    return JsonResponse({"result": result})


def get_enrollment_orders(request):
    result = ""
    return JsonResponse({"result": result})


def get_citizenship(request):
    result = Citizenship.get_citizenship()
    return JsonResponse({"result": result})


def get_application_filters(request):
    sources = []
    statuses = []
    stages = []
    return JsonResponse({"sources": sources, "statuses": statuses, "stages": stages})


def get_exams_filters(request):
    exam_types = ExamType.get_types()
    subjects = Subjects.get_subjects()
    return JsonResponse({"exam_types": exam_types, "subjects": subjects})


def get_achievements_filters(request):
    achievements = AchievementType.get_types()
    statuses = []
    return JsonResponse({"achievements": achievements, "statuses": statuses})


def get_education(request):
    result = DocumentTypeEducation.get_education_documents_tree()
    return JsonResponse({"result": result})


def get_special_rights(request):
    result = SpecialRights.get_special_rights_tree()
    return JsonResponse({"result": result})


def get_enrollees(request):
    data = get_all_enrollees(request)
    columns = [
        {"field": 'card', "key": 'card', "title": 'Дело'},
        {"field": 'fio', "key": 'fio', "title": 'ФИО'},
        {"field": 'application', "key": 'application', "title": 'Заявление'},
        {"field": 'сhemistry', "key": 'сhemistry', "title": 'Хим.'},
        {"field": 'biology', "key": 'biology', "title": 'Био.'},
        {"field": 'mathematics', "key": 'mathematics', "title": 'Мат.'},
        {"field": 'russian_language', "key": 'russian_language', "title": 'Рус.'},
        {"field": 'achievement', "key": 'achievement', "title": 'ИД'},
        {"field": 'achievementСhecked', "key": 'achievementСhecked', "title": 'ИД+'},
        {"field": 'amount', "key": 'amount', "title": 'Сумм'},
        {"field": 'is_original', "key": 'is_original', "title": 'Оригинал'},
        {"field": 'status', "key": 'status', "title": 'Статус'},
        {"field": 'create_date', "key": 'create_date', "title": 'Создано'},
    ]
    return JsonResponse({"data": data, "columns": columns})


def get_applications_by_card(request):
    request_data = json.loads(request.body)
    result = ApplicationEducation.get_applications_by_card(request_data["card_pk"])
    return JsonResponse({"result": result})
