from django.urls import path

from . import views

urlpatterns = [
    path('fractions', views.fractions),
    path('units', views.units),
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
    path('last-received-daynum', views.last_received_daynum),
    path('receive-one-by-one', views.receive_one_by_one),
    path('receive-history', views.receive_history),
    path('save-defect-tube', views.save_defect_tube),
    path('construct/get-departments', views.get_departments),
    path('construct/get-tubes', views.get_tubes),
    path('construct/update-order-research', views.update_order_research),
    path('construct/change-visibility-research', views.change_visibility_research),
    path('construct/get-research', views.get_research),
]
