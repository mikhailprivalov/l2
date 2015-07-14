from django.contrib import admin
from .models import DoctorProfile

admin.site.register(DoctorProfile)  # Активация редактирования профилей врачей в админке
