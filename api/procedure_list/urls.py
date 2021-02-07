from django.urls import path
from . import views


urlpatterns = [
    path('get-procedure', views.get_procedure_by_dir),
    path('procedure-cancel', views.procedure_cancel),
    path('procedure-time-execute', views.procedure_execute),
    path('params', views.params),
    path('department-procedures', views.procedure_aggregate),
    path('department-all', views.get_podrazdeleniya_predural_list),
]
