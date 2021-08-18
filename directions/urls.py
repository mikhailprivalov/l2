from django.urls import path

from . import views

urlpatterns = [
    path('pdf', views.gen_pdf_dir),
    path('execlist', views.gen_pdf_execlist),
    path('def', views.setdef),
    path('get/one', views.get_one_dir),
    path('get/issledovaniya', views.get_issledovaniya),
    path('order_researches', views.order_researches),
]
