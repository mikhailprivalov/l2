from django.urls import path

from . import views

urlpatterns = [
    path('result/next', views.next_result_direction),
    path('result/amd', views.get_dir_amd),
    path('result/n3', views.get_dir_n3),
    path('result/resend-l2', views.get_dir_n3),
    path('result/sendamd', views.result_amd_send),
    path('direction/data', views.direction_data),
    path('iss/data', views.issledovaniye_data),
    path('iss/data-multi', views.issledovaniye_data_multi),
    path('set-core-id', views.set_core_id),
    path('check-enp', views.check_enp),
    path('get-patient-results-covid19', views.patient_results_covid19),
    path('log', views.make_log),
    path('doc-call-create', views.external_doc_call_create),
    path('doc-call-update-status', views.external_doc_call_update_status),
    path('doc-call-send', views.external_doc_call_send),
    path('send-result', views.external_research_create),
    path('eds/get-user-data', views.eds_get_user_data),
    path('eds/get-cda-data', views.eds_get_cda_data),
]
