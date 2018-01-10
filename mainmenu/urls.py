from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.dashboard),
    path('directions/multiprint', views.dir_multiprint),
    path('direction/info', views.direction_info),
    path('biomaterial/get', views.researches_control),
    path('create_user', views.create_user),
    path('from', views.dashboard_from),
    path('create_podr', views.create_pod),
    path('ldap_sync', views.ldap_sync),
    path('directions', views.directions),
    path('directions_ng', login_required(TemplateView.as_view(template_name="dashboard/directions_ng.html"))),
    path('receive/journal_form', views.receive_journal_form),
    path('view_log', views.view_log),
    path('confirm_reset', views.confirm_reset),
    path('view_logs', views.load_logs),
    path('users/count', views.users_count),
    path('users/ldap/dosync', views.users_dosync),
    path('results_history', views.results_history),  # TemplateView.as_view(template_name="dashboard/results_history.html")),
    path('results_fastprint', TemplateView.as_view(template_name="dashboard/results_fastprint.html", )),
    path('utils', TemplateView.as_view(template_name="dashboard/utils.html", )),
    path('results_history/search', views.results_history_search),
    path('change_password', views.change_password),
    path('update_pass', views.update_pass),
    path('discharge', views.discharge),
    path('discharge/send', views.discharge_add),
    path('discharge/search', views.discharge_search),
    path('researches_from_directions', views.researches_from_directions),
    path('cards', views.cards),
]
