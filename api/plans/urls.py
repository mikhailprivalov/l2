from django.urls import path
from . import views


urlpatterns = [
    path('plan-operations-save', views.plan_operations_save),
    path('get-plan-operations-by-patient', views.get_plan_operations_by_patient),
    path('get-plan-by-params', views.get_plan_operations_by_params),
    path('departments-can-operate', views.get_departments_can_operate),
    path('change-anestesiolog', views.change_anestesiolog),
    path('plan-operations-cancel', views.plan_operations_cancel),
    path('get-plan-hospitalization', views.get_plan_hospitalization_by_params),
]
