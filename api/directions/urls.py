from django.urls import path
from . import views

urlpatterns = [
    path('generate', views.directions_generate),
    path('rmis-directions', views.directions_rmis_directions),
    path('rmis-direction', views.directions_rmis_direction),
    path('history', views.directions_history),
    path('cancel', views.directions_cancel),
    path('results', views.directions_results),
    path('services', views.directions_services),
    path('mark-visit', views.directions_mark_visit),
    path('receive-material', views.directions_receive_material),
    path('visit-journal', views.directions_visit_journal),
    path('recv-journal', views.directions_recv_journal),
    path('last-result', views.directions_last_result),
    path('results-report', views.directions_results_report),
    path('paraclinic_form', views.directions_paraclinic_form),
    path('paraclinic_result', views.directions_paraclinic_result),
    path('paraclinic_result_confirm', views.directions_paraclinic_confirm),
    path('paraclinic_result_confirm_reset', views.directions_paraclinic_confirm_reset),
    path('paraclinic_result_history', views.directions_paraclinic_history),
    path('patient-history', views.directions_patient_history),
    path('data-by-fields', views.directions_data_by_fields),
    path('last-fraction-result', views.last_fraction_result),
]
