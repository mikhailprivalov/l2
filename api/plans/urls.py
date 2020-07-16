from django.urls import path
from . import views


urlpatterns = [
    path('plan-operations-save', views.plan_operations_save),
    path('get-plan-operations-by-patient', views.get_plan_operations_by_patient),
]
