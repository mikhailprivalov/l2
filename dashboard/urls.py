from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^dashboard/directions/multiprint', views.dir_multiprint),
    url(r'^dashboard/researches/control$', views.researches_control),
    url(r'^dashboard/create_user$', views.create_user),
    url(r'^dashboard/from$', views.dashboard_from),
    url(r'^dashboard/create_podr$', views.create_pod),
    url(r'^dashboard/ldap_sync$', views.ldap_sync),
    url(r'^dashboard/directions$', views.directions),
    url(r'^dashboard/receive/journal_form$', views.receive_journal_form),
    url(r'^dashboard/view_log$', views.view_log),
    url(r'^dashboard/confirm_reset$$', views.confirm_reset),
    url(r'^dashboard/view_logs$', views.load_logs),
    url(r'^dashboard/users/count$', views.users_count),
    url(r'^dashboard/users/ldap/dosync$', views.users_dosync),
]
