from django.urls import path
from api.working_time import views

urlpatterns = [
    path('get-departments', views.get_departments),
    path('get-work-time', views.get_work_time),
    path('update-time', views.update_time),
    path('create-document', views.create_document),
    path('get-ref-books', views.get_ref_books),
    path('employee-transfer', views.employee_transfer),
    path('get-work-time-filling-by-employee-template', views.get_work_time_filling_by_employee_template),
    path('edit-lunch', views.edit_lunch),
    path('get-holidays', views.get_holidays),
]
