from django.urls import path
from api.working_time import views

urlpatterns = [
    path('get-departments', views.get_departments),
    path('get-work-time', views.get_work_time),
    path('update-time', views.update_time),
    path('create-document', views.create_document),
    path('get-ref-books', views.get_ref_books),
    path('print-document', views.print_document),
    path('employee-transfer', views.employee_transfer),
]
