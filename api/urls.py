from django.urls import path

from . import views

urlpatterns = [
    path('send', views.send),
    path('endpoint', views.endpoint),
    path('departments', views.departments),
    path('bases', views.bases),
    path('researches/templates', views.ResearchesTemplates.as_view()),
    path('researches/all', views.Researches.as_view()),
    path('current-user-info', views.current_user_info),
    path('directive-from', views.directive_from),
    path('patients/search-card', views.patients_search_card),
    path('directions/generate', views.directions_generate),
]
