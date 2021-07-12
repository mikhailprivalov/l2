from django.contrib import admin
from .models import DoctorScheduleResource, ResourceSlotsPlan, ResourceSlotsFact


admin.site.register(DoctorScheduleResource)
admin.site.register(ResourceSlotsPlan)
admin.site.register(ResourceSlotsFact)
