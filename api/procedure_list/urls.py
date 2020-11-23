from django.urls import path
from . import views


urlpatterns = [
    path('get-procedure', views.get_procedure_by_dir),
    path('procedure-cancel', views.procedure_cancel),
    path('params', views.params),
]
