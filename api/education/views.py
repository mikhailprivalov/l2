from django.http import JsonResponse

from laboratory.settings import (
    EDUCATIONDIRECTIONS,
    PAYFORM,
    COMPANIES,
    ENROLLMENTSTATUSES,
    DEDUCTIONSTATUSES,
    COMMANDS,
    CITEZENSHIP,
    STATEMENTSOURCES,
    STATEMENTSTATUSES,
    STATEMENTSSTAGES,
    TYPESEXAM,
    SUBJECTS,
    EXAMSTATUSES,
    TYPEIA,
    IASTATUSES,
    SATISFACTORYBALLS,
    EDUCATION,
    SPECIALRIGHTS,
)


def get_education_directions(request):
    result = EDUCATIONDIRECTIONS
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


def get_commands(request):
    result = COMMANDS
    return JsonResponse({"result": result})


def get_citezenship(request):
    result = CITEZENSHIP
    return JsonResponse({"result": result})


def get_statement_sources(request):
    result = STATEMENTSOURCES
    return JsonResponse({"result": result})


def get_statement_statuses(request):
    result = STATEMENTSTATUSES
    return JsonResponse({"result": result})


def get_statement_stages(request):
    result = STATEMENTSSTAGES
    return JsonResponse({"result": result})


def get_exam_types(request):
    result = TYPESEXAM
    return JsonResponse({"result": result})


def get_subjects(request):
    result = SUBJECTS
    return JsonResponse({"result": result})


def get_exam_statuses(request):
    result = EXAMSTATUSES
    return JsonResponse({"result": result})


def get_ia_types(request):
    result = TYPEIA
    return JsonResponse({"result": result})


def get_ia_statuses(request):
    result = IASTATUSES
    return JsonResponse({"result": result})


def get_satisfactory_balls(request):
    result = SATISFACTORYBALLS
    return JsonResponse({"result": result})


def get_education(request):
    result = EDUCATION
    return JsonResponse({"result": result})


def get_special_rights(request):
    result = SPECIALRIGHTS
    return JsonResponse({"result": result})
