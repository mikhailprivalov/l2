from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('pdf', views.pdf),
    path('preview', TemplateView.as_view(template_name='dashboard/stattalon_preview.html')),
]

