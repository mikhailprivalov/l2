from django.urls import path

from api.reports import views

urlpatterns = [
    path('statistic-params-search', views.statistic_params_search),
    path('xlsx-model', views.xlsx_model),
]
