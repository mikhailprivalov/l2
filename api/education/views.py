from django.http import JsonResponse

from laboratory.settings import (
    SPECIALTIES,
    PAYFORM,
    COMPANIES,
    ENROLLMENTSTATUSES,
    DEDUCTIONSTATUSES,
    ENROLLMENTORDERS,
    CITIZENSHIP,
    STATEMENTSOURCES,
    STATEMENTSTATUSES,
    STATEMENTSSTAGES,
    EXAMS,
    EXAMSUBJECTS,
    EXAMSTATUSES,
    ACHIEVEMENTS,
    ACHIEVEMENTSSTATUSES,
    SATISFACTORYBALLS,
    EDUCATIONS,
    SPECIALRIGHTS,
    ENROLLEES,
)


def get_specialties(request):
    result = SPECIALTIES
    return JsonResponse({"result": result})


def get_pay_forms(request):
    result = PAYFORM
    return JsonResponse({"result": result})


def get_companies(request):
    result = COMPANIES
    return JsonResponse({"result": result})


def get_enrollment_statuses(request):
    result = ENROLLMENTSTATUSES
    return JsonResponse({"result": result})


def get_deduction_statuses(request):
    result = DEDUCTIONSTATUSES
    return JsonResponse({"result": result})


def get_enrollment_orders(request):
    result = ENROLLMENTORDERS
    return JsonResponse({"result": result})


def get_citizenship(request):
    result = CITIZENSHIP
    return JsonResponse({"result": result})


def get_statement_filters(request):
    sources = STATEMENTSOURCES
    statuses = STATEMENTSTATUSES
    stages = STATEMENTSSTAGES
    return JsonResponse({"sources": sources, "statuses": statuses, "stages": stages})


def get_exams_filters(request):
    exams = EXAMS
    subjects = EXAMSUBJECTS
    statuses = EXAMSTATUSES
    return JsonResponse({"exams": exams, "subjects": subjects, "statuses": statuses})


def get_achievements_filters(request):
    achievements = ACHIEVEMENTS
    statuses = ACHIEVEMENTSSTATUSES
    return JsonResponse({"achievements": achievements, "statuses": statuses})


def get_satisfactory_balls(request):
    result = SATISFACTORYBALLS
    return JsonResponse({"result": result})


def get_education(request):
    result = EDUCATIONS
    return JsonResponse({"result": result})


def get_special_rights(request):
    result = SPECIALRIGHTS
    return JsonResponse({"result": result})


def get_enrollees(request):
    result = ENROLLEES
    return JsonResponse({"result": result})
