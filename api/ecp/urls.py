from django.urls import path

from . import views

urlpatterns = [
    path('available-slots-of-dates', views.get_available_slots_of_dates),
    path('available-slots', views.get_available_slots),
    path('fill-slot', views.fill_slot),
    path('cancel-slot', views.cancel_slot),

]
