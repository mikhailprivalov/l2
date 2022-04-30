from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

import receivematerial.views
from . import views

urlpatterns = [
    path('', views.dashboard),
    path('directions/multiprint', views.dir_multiprint),
    path('biomaterial/get', views.researches_control),
    path('from', views.dashboard_from),
    path('create_podr', views.create_pod),
    path('ldap_sync', views.ldap_sync),
    path('directions', views.directions),
    path('receive/journal_form', views.receive_journal_form),
    path('view_log', views.view_log),
    path('confirm_reset', views.confirm_reset),
    path('view_logs', views.load_logs),
    path('users/count', views.users_count),
    path('results_history', views.results_history),  # TemplateView.as_view(template_name="dashboard/results_history.html")),
    path('results_report', views.results_report),
    path('results_fastprint', TemplateView.as_view(template_name="dashboard/results_fastprint.html")),
    path('results_department', views.results_department),
    path('utils', TemplateView.as_view(template_name="dashboard/utils.html")),
    path('results_history/search', views.results_history_search),
    path('profiles', views.profiles),
    path('discharge', views.discharge),
    path('discharge/send', views.discharge_add),
    path('discharge/search', views.discharge_search),
    path('researches_from_directions', views.researches_from_directions),
    path('direction_visit', views.direction_visit),
    path('results/paraclinic', views.results_paraclinic),
    path('results/paraclinic/blanks', views.results_paraclinic_blanks),
    path('receive', receivematerial.views.receive),
    path('receive/one_by_one', receivematerial.views.receive_obo),
    path('receive/execlist', receivematerial.views.receive_execlist),
    path('receive/last_received', receivematerial.views.last_received),
    path('receive/history', receivematerial.views.receive_history),
    path('receive/journal', receivematerial.views.receive_journal),
    path('rmq', staff_member_required(TemplateView.as_view(template_name="dashboard/rmq.html"))),
    path('rmq/messages', views.rmq_messages),
    path('rmq/count', views.rmq_count),
    path('rmq/send', views.rmq_send),
    path('stationar', login_required(TemplateView.as_view(template_name="dashboard/stationar.html"))),
    path('list_wait', views.list_wait),
    path('doc_call', views.doc_call),
    path('procedure_list', TemplateView.as_view(template_name="dashboard/procedure_list.html")),
]
