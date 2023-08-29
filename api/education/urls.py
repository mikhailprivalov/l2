from django.urls import path

from . import views

urlpatterns = [
    path('get-specialties', views.get_specialties),
    path('get-pay-forms', views.get_pay_forms),
    path('get-enrollment-orders', views.get_enrollment_orders),
    path('get-citizenship', views.get_citizenship),
    path('get-statement-filters', views.get_application_filters),
    path('get-exams-filters', views.get_exams_filters),
    path('get-achievements-filters', views.get_achievements_filters),
    path('get-educations', views.get_education),
    path('get-special-rights', views.get_special_rights),
    path('get-applications', views.get_applications),
]
