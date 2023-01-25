from django.urls import path

from . import views

urlpatterns = [
    path('departments/list', views.departments_list),
    path('departments/add', views.departments_add),
    path('departments/edit', views.departments_edit),
    path('departments/form-info', views.departments_form_info),
    path('departments/treeselect', views.departments_treeselect),
    path('departments/get', views.departments_get),
    path('positions/list', views.positions_list),
    path('positions/add', views.positions_add),
    path('positions/edit', views.positions_edit),
    path('positions/treeselect', views.positions_treeselect),
    path('positions/get', views.positions_get),
    path('employees/list', views.employees_list),
    path('employees/add', views.employees_add),
    path('employees/edit', views.employees_edit),
    path('employees/get', views.employees_get),
    path('employees/treeselect', views.employees_treeselect),
]
