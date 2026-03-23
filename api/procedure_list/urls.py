from django.urls import path
from . import views


urlpatterns = [
    path('get-procedure', views.get_procedure_by_dir),
    path('procedure-cancel', views.procedure_cancel),
    path('procedure-time-execute', views.procedure_execute),
    path('params', views.params),
    path('department-procedures', views.procedure_aggregate),
    path('suitable-departments', views.get_suitable_departments),
    path('procedure-for-extract', views.procedure_for_extract),
    path('get-templates', views.get_templates),
    path('get-selected-template-data', views.get_selected_template_data),
    path('find-template-for-edit-or-add', views.find_template_for_edit_or_add),
    path('add-template', views.add_template),
    path('edit-template', views.edit_template),
]
