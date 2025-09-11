from django.urls import path

from . import views

urlpatterns = [
    path('list', views.get_requests),
    path('equipment', views.get_equipment_list),
    path('images', views.get_request_images),
    path('image-details', views.get_image_details),
    path('request-details', views.get_request_details),
    path('create', views.create_request),
    path('link-image', views.link_image_to_request),
    path('unlinked-requests', views.get_unlinked_requests),
    path('by-status', views.get_requests_by_status),
    path('accept', views.accept_request),
    path('cancel-accept', views.cancel_accept_request),
    path('params', views.get_request_params),
]
