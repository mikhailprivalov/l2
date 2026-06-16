from django.urls import path

from . import views

urlpatterns = [
    path("protocol-docx", views.protocol_docx),
    path("protocol-docx-xml", views.protocol_docx_xml),
]
