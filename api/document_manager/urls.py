from django.urls import path

from . import views

urlpatterns = [
    path('groups/list', views.groups_list),
    path('groups/update', views.groups_update),
    path('types/list', views.types_list),
    path('types/update', views.types_update),
    path('cases/list', views.cases_list),
    path('cases/update', views.cases_update),
    path('structure/details', views.structure_details),
    path('structure/update', views.structure_update),
    path('documents/list', views.documents_list),
    path('documents/find', views.documents_find),
    path('documents/recent', views.documents_recent),
    path('documents/create', views.documents_create),
    path('documents/details', views.documents_details),
    path('documents/save', views.documents_save),
    path('documents/confirm', views.documents_confirm),
    path('documents/confirm-reset', views.documents_confirm_reset),
    path('documents/hide', views.documents_hide),
    path('documents/history', views.documents_history),
    path('addressees/groups/list', views.addressees_groups_list),
    path('addressees/groups/details', views.addressees_groups_details),
    path('addressees/groups/update', views.addressees_groups_update),
    path('addressees/groups/save-personal', views.addressees_groups_save_personal),
    path('addressees/groups/delete', views.addressees_groups_delete),
    path('addressees/employees', views.addressees_employees),
]
