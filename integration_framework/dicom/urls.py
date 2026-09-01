from django.urls import path
from . import views

urlpatterns = [
    path('get-meta-tags', views.get_meta_tags),
    path('dcm-order-create', views.dcm_order_create),
    path('dcm-order-create-status', views.dcm_order_create_status),
    path('dcm-study-link', views.dcm_study_link),
    path('dcm-study-link-status', views.dcm_study_link_status),
    path('json-order-create', views.json_order_create),
    path('json-study-link', views.json_study_link),
    path('json-order-get', views.json_order_get),
    path('json-result-create', views.json_result_create),
]
