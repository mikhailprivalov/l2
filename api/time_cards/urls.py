from django.urls import path
from . import views


urlpatterns = [
    path('staff-load-department', views.staf_load_department),
    path('staff-update-department', views.staff_update_department),
    path('staff-load-employee', views.staff_load_employee),
    path('staff-update-employee', views.staff_update_employee),
    path('staff-load-posts', views.staff_load_posts),
    path('staff-update-post', views.staff_update_post),
    path('staff-load-post', views.staff_load_post),

    path('staff-result-tabel', views.staff_result_tabel),
    path('staff-change-status-tabel', views.staff_change_status_tabel),
]
