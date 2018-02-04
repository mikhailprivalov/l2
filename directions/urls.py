from django.urls import path

from . import views

urlpatterns = [
    path('resend', views.resend),
    path('pdf', views.gen_pdf_dir),
    path('execlist', views.gen_pdf_execlist),
    path('def', views.setdef),
    path('get/one', views.get_one_dir),
    path('get/issledovaniya', views.get_issledovaniya),
    path('worklist', views.get_worklist),
    path('order_researches', views.order_researches),
    path('group_confirm_get', views.group_confirm_get),
]
