from django.urls import path
from django.views.generic import TemplateView

import receivematerial.views
from . import views

urlpatterns = [
    path('', views.dashboard),
    path('biomaterial/get', views.researches_control),
    path('from', views.dashboard_from),
    path('directions', views.directions),
    path('view_log', views.view_log),
    path('view_logs', views.load_logs),
    path('users/count', views.users_count),
    path('results_history', views.results_history),
    path('results_report', views.results_report),
    path('results_fastprint', TemplateView.as_view(template_name="dashboard/results_fastprint.html")),
    path('results_department', views.results_department),
    path('utils', TemplateView.as_view(template_name="dashboard/utils.html")),
    path('results_history/search', views.results_history_search),
    path('profiles', views.profiles),
    path('researches_from_directions', views.researches_from_directions),
    path('direction_visit', views.direction_visit),
    path('results/paraclinic', views.results_paraclinic),
    path('results/paraclinic/blanks', views.results_paraclinic_blanks),
    path('receive', receivematerial.views.receive),
    path('receive/execlist', receivematerial.views.receive_execlist),
    path('receive/journal', receivematerial.views.receive_journal),
    path('list_wait', views.list_wait),
    path('doc_call', views.doc_call),
    path('procedure_list', TemplateView.as_view(template_name="dashboard/procedure_list.html")),
]
