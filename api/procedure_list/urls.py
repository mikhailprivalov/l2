from django.urls import path
from . import views


urlpatterns = [
    path('procedure-save', views.procedure_save),
    path('get-procedure', views.get_procedure_by_dir),
    path('procedure-cancel', views.procedure_cancel),
]
