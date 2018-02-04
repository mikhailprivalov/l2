from django.urls import path

import researches.views
from . import views

urlpatterns = [
    path('tubes/all', researches.views.get_all_tubes),
    path('tubes', researches.views.tubes_control),
    path('tubes/relation', researches.views.tubes_relation),
    path('research', views.directory_research),
    path('researches', views.directory_researches),
    path('researches/sort', views.directory_researches_update_sort),
    path('researches/hide/toggle', views.directory_toggle_hide_research),
    path('researches/copy', views.directory_copy_research),
    path('researches/group', views.directory_researches_group),
    path('researches/directions', views.directory_get_directions),
    path('researches/list', views.directory_researches_list),
    path('researches/update_uet', views.directory_researches_update_uet),
    path('researches/update_mode', views.directory_researches_update_mode),
    path('researches/update_template', views.researches_update_template),
]
