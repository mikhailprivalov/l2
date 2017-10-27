from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^log$', views.log),
    url(r'^log/cleanup$', views.log_cleanup),
    url(r'^db$', views.db),
    url(r'^rmis/check$', views.rmis_check),
    url(r'^archive_cards$', views.archive_without_directions),
    url(r'^patients$', views.patients_without_cards),
    url(r'^sync/departments$', views.sync_departments),
    url(r'^sync/researches$', views.sync_researches),
]
