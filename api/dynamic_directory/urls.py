from django.urls import path

from . import views

urlpatterns = [
    path('list', views.list_directories),
    path('list-treeselect', views.list_directories_treeselect),
    path('get', views.get_directory),
    path('rows', views.get_directory_rows),
    path('one-row', views.get_directory_one_row),
    path('suggests', views.get_suggests),
    path('record-for-edit', views.record_for_edit),
    path('save-record', views.save_record),
]
