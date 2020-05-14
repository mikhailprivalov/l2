from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('search', views.results_search),
    path('search/directions', views.results_search_directions),
    path('enter', views.enter),
    path('save', views.results_save),
    path('loadready', views.loadready),
    path('get', views.result_get),
    path('confirm', views.result_confirm),
    path('confirm/list', views.result_confirm_list),
    path('pdf', views.result_print),
    path('preview', TemplateView.as_view(template_name='dashboard/results_preview.html')),
    path('journal', views.result_journal_print),
    path('journal_table', views.result_journal_table_print),
    path('filter', views.result_filter),
    path('day', views.get_day_results),
]
