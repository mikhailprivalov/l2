from django.urls import path

from . import views

urlpatterns = [
    path('send', views.send),
    path('endpoint', views.endpoint),
    path('departments', views.departments),
    path('bases', views.bases),
    path('researches/templates', views.ResearchesTemplates.as_view()),
    path('researches/all', views.Researches.as_view()),
    path('researches/by-department', views.researches_by_department),
    path('researches/update', views.researches_update),
    path('researches/details', views.researches_details),
    path('researches/descriptive_details', views.descriptive_details),
    path('current-user-info', views.current_user_info),
    path('directive-from', views.directive_from),
    path('patients/search-card', views.patients_search_card),
    path('directions/generate', views.directions_generate),
    path('directions/history', views.directions_history),
    path('directions/cancel', views.directions_cancel),
    path('directions/results', views.directions_results),
    path('directions/descriptive_form', views.directions_descriptive_form),
    path('directions/descriptive_result', views.directions_descriptive_result),
    path('directions/descriptive_result_confirm', views.directions_descriptive_confirm),
    path('directions/descriptive_result_confirm_reset', views.directions_descriptive_confirm_reset),
    path('directions/descriptive_result_history', views.directions_descriptive_history),
    path('statistics-tickets/types', views.statistics_tickets_types),
    path('statistics-tickets/send', views.statistics_tickets_send),
    path('statistics-tickets/get', views.statistics_tickets_get),
    path('statistics-tickets/invalidate', views.statistics_tickets_invalidate),
]
