from django.urls import path
from . import views

urlpatterns = [
    path('templates', views.ResearchesTemplates.as_view()),
    path('all', views.Researches.as_view()),
    path('by-department', views.researches_by_department),
    path('params', views.researches_params),
    path('update', views.researches_update),
    path('details', views.researches_details),
    path('paraclinic_details', views.paraclinic_details),
    path('hosp-service-details', views.hospital_service_details),
    path('fast-templates', views.fast_templates),
    path('fast-template-data', views.fast_template_data),
    path('fast-template-save', views.fast_template_save),
    path('fraction-title', views.fraction_title),
    path('field-title', views.field_title),
]
