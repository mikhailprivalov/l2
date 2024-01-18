from django.urls import path

from . import views

urlpatterns = [
    path('laboratory/get-departments', views.get_lab_departments),
    path('laboratory/get-tubes', views.get_tubes),
    path('laboratory/update-order-research', views.update_order_research),
    path('laboratory/change-visibility-research', views.change_visibility_research),
    path('laboratory/get-research', views.get_lab_research),
    path('laboratory/update-research', views.update_lab_research),
    path('laboratory/get-ref-books', views.get_lab_ref_books),
]
