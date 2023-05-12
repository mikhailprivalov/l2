from django.urls import path

from . import views

urlpatterns = [
    path('get-unallocated-patients', views.get_unallocated_patients),
    path('get-chambers-and-beds', views.get_chambers_and_beds),
    path('entrance-patient-to-bed', views.entrance_patient_to_bed),
    path('extract-patient-bed', views.extract_patient_bed),
    path('get-attending-doctors', views.get_attending_doctors),
    path('update-doctor-to-bed', views.update_doctor_to_bed),
    path('get-patients-without-bed', views.get_patients_without_bed),
    path('save-patient-without-bed', views.save_patient_without_bed),
    path('delete-patient-without-bed', views.delete_patient_without_bed),
]
