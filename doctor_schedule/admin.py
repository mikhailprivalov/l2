from django.contrib import admin
from .models import ScheduleResource, SlotPlan, SlotFact


admin.site.register(ScheduleResource)
admin.site.register(SlotPlan)
admin.site.register(SlotFact)
