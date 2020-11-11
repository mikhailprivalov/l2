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
    path('log', views.make_log),
    path('doc-call-create', views.external_doc_call_create),
    path('research-create', views.external_research_create),
]
