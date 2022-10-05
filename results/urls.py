from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('search/directions', views.results_search_directions),
    path('enter', views.enter),
    path('get', views.result_get),
    path('pdf', views.result_print),
    path('preview', views.results_preview),
    path('results', views.results),
    path('journal', views.result_journal_print),
    path('journal_table', views.result_journal_table_print),
    path('day', views.get_day_results),
]
