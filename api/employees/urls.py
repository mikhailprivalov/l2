from django.urls import path

from . import views

urlpatterns = [
    path('get-organizations', views.get_organizations),
    path('get-ref-books', views.get_ref_books),
]
