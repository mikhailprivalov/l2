from django.urls import path

from . import views

urlpatterns = [
    path('fractions', views.fractions),
    path('fraction', views.fraction),
    path('save-fsli', views.save_fsli),
    path('laboratories', views.laboratories),
    path('ready', views.ready),
    path('search', views.search),
    path('form', views.form),
    path('save', views.save),
    path('confirm', views.confirm),
    path('confirm-list', views.confirm_list),
    path('reset-confirm', views.reset_confirm),
]
