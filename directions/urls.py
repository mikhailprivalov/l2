from django.urls import path

from . import views

urlpatterns = [
    path('pdf', views.gen_pdf_dir),
    path('execlist', views.gen_pdf_execlist),
    path('order_researches', views.order_researches),
]
