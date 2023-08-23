from django.urls import path

from . import views

urlpatterns = [
    path('get-education-directions', views.get_education_directions),
    path('get-pay-forms', views.get_pay_forms),
    path('get-companies', views.get_companies),
    path('get-enrollment-statuses', views.get_enrollment_statuses),
    path('get-deduction-statuses', views.get_deduction_statuses),
    path('get-commands', views.get_commands),
    path('get-citezenship', views.get_citezenship),
    path('get-statement-sources', views.get_statement_sources),
    path('get-statement-statuses', views.get_statement_statuses),
    path('get-statement_stages', views.get_statement_stages),
    path('get-exam-types', views.get_exam_types),
    path('get-subjects', views.get_subjects),
    path('get-exam-statuses', views.get_exam_statuses),
    path('get-ia-types', views.get_ia_types),
    path('get-ia-statuses', views.get_ia_statuses),
    path('get-satisfactory-balls', views.get_satisfactory_balls),
    path('get-education', views.get_education),
    path('get-special-rights', views.get_special_rights),
]
