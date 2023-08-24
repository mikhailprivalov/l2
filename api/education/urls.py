from django.urls import path

from . import views

urlpatterns = [
    path('get-specialties', views.get_specialties),
    path('get-pay-forms', views.get_pay_forms),
    path('get-companies', views.get_companies),
    path('get-enrollment-statuses', views.get_enrollment_statuses),
    path('get-deduction-statuses', views.get_deduction_statuses),
    path('get-enrollment-orders', views.get_enrollment_orders),
    path('get-citizenship', views.get_citizenship),
    path('get-statement-filters', views.get_statement_filters),
    path('get-exams-filters', views.get_exams_filters),
    path('get-achievements-filters', views.get_achievements_filters),
    path('get-satisfactory-balls', views.get_satisfactory_balls),
    path('get-educations', views.get_education),
    path('get-special-rights', views.get_special_rights),
    path('get-enrollees', views.get_enrollees),
]
