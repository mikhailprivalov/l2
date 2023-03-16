from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('pdf', views.pdf),
    path('docx', views.docx),
    path('preview', TemplateView.as_view(template_name='dashboard/stattalon_preview.html')),
    path('extra-nofication', views.extra_nofication),
    path('covid-result', views.covid_result),
    path('json-nofication', views.json_nofication),
]
