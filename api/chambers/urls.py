from django.urls import path

from . import views

urlpatterns = [
    path('get-unallocated-patients', views.get_unallocated_patients),
    path('get-chambers-and-beds', views.get_chambers_and_beds),
    # path('get-beds', views.get_beds),
    path('entrance-patient-to-bed', views.entrance_patient_to_bed),
    path('extract-patient-bed', views.extract_patient_bed),
    path('doctor-assigned-patient', views.doctor_assigned_patient),
    path('get-attending-doctor', views.get_attending_doctor),
    path('doctor-detached-patient', views.doctor_detached_patient),
]
