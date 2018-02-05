from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

import receivematerial.views
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name="reports.html")),
]
