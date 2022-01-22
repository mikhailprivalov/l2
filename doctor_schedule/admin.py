from django.contrib import admin
from .models import ScheduleResource, SlotPlan, SlotFact


class ScheduleResourceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'executor', 'room', 'department', 'speciality')
    autocomplete_fields = ('executor', 'room', 'department',)
    search_fields = ('pk', 'executor', 'room', 'department', 'speciality')


class SlotPlanAdmin(admin.ModelAdmin):
    list_display = ('pk', 'resource', 'datetime', 'duration_minutes', 'available_systems', 'disabled')
    autocomplete_fields = ('resource',)
    search_fields = ('pk', 'resource', 'datetime', 'duration_minutes', 'available_systems')


class SlotFactAdmin(admin.ModelAdmin):
    list_display = ('pk', 'plan', 'patient', 'status', 'external_slot_id')
    autocomplete_fields = ('plan', 'patient', 'research')
    search_fields = ('pk', 'plan', 'patient', 'status', 'external_slot_id')
    raw_id_fields = ('direction',)


admin.site.register(ScheduleResource, ScheduleResourceAdmin)
admin.site.register(SlotPlan, SlotPlanAdmin)
admin.site.register(SlotFact, SlotFactAdmin)
