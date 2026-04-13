from django.urls import path
from . import views

urlpatterns = [
    path('get-meta-tags', views.get_meta_tags),
    path('dcm-order-create', views.dcm_order_create),
    path('dcm-study-link', views.dcm_study_link),
]
