from django.urls import path

from . import views

urlpatterns = [
    path('days', views.days),
    path('details', views.details),
    path('save', views.save),
    path('cancel', views.cancel),
    path('save-resource', views.save_resource),
    path('search-resource', views.search_resource),
    path('get-first-user-resource', views.get_first_user_resource),
    path('create-slots', views.create_slots),
    path('available-slots', views.available_slots),
    path('available-hospitalization-plan', views.available_hospitalization_plan),
    path('check-hosp-slot-before-save', views.check_hosp_slot_before_save),
    path('available-slots-of-dates', views.available_slots_of_dates),
    path('schedule-access', views.schedule_access),
]
