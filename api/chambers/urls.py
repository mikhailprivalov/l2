from django.urls import path

from . import views

urlpatterns = [
    path('get-unallocated-patients', views.get_unallocated_patients),
    path('get-chambers-and-beds', views.get_chambers_and_beds),
    path('get-hospitalization-calendar', views.get_hospitalization_calendar),
    path('get-accompanying-child-options', views.get_accompanying_child_options),
    path('entrance-patient-to-bed', views.entrance_patient_to_bed),
    path('save-hospitalization-by-fio', views.save_hospitalization_by_fio),
    path('move-hospitalization-to-bed', views.move_hospitalization_to_bed),
    path('update-hospitalization-record', views.update_hospitalization_record),
    path('set-hospitalization-day-hosp', views.set_hospitalization_day_hosp),
    path('clear-patient-from-bed', views.clear_patient_from_bed),
    path('extract-patient-bed', views.extract_patient_bed),
    path('get-attending-doctors', views.get_attending_doctors),
    path('update-doctor-to-bed', views.update_doctor_to_bed),
    path('get-patients-without-bed', views.get_patients_without_bed),
    path('get-directions-hosp-meta', views.get_directions_hosp_meta),
    path('save-patient-without-bed', views.save_patient_without_bed),
    path('delete-patient-without-bed', views.delete_patient_without_bed),
]
