from django.contrib import admin
from .models import ScheduleResource, SlotPlan, SlotFact, UserResourceModifyRights, ReasonCancelSlot, SlotFactCancel


class ScheduleResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'executor', 'room', 'department', 'speciality')
    autocomplete_fields = (
        'executor',
        'room',
        'department',
    )
    search_fields = ('title', 'executor', 'service', 'room', 'department', 'speciality')
    filter_horizontal = ('service',)


class SlotPlanAdmin(admin.ModelAdmin):
    list_display = ('pk', 'resource', 'datetime', 'duration_minutes', 'available_systems', 'disabled')
    autocomplete_fields = ('resource',)
    search_fields = ('pk', 'resource', 'datetime', 'duration_minutes', 'available_systems')


class SlotFactAdmin(admin.ModelAdmin):
    list_display = ('pk', 'plan', 'patient', 'status', 'external_slot_id')
    autocomplete_fields = ('plan', 'patient', 'service')
    search_fields = ('pk', 'plan', 'patient', 'status', 'external_slot_id')
    raw_id_fields = ('direction',)


class UserResourceModifyRightsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user')
    autocomplete_fields = ('user',)
    search_fields = ('pk', 'user')
    filter_horizontal = ('resources', 'departments', 'services')


class SlotFactCancelAdmin(admin.ModelAdmin):
    list_display = ('pk', 'plan', 'patient')
    search_fields = ('plan',)


admin.site.register(ScheduleResource, ScheduleResourceAdmin)
admin.site.register(SlotPlan, SlotPlanAdmin)
admin.site.register(SlotFact, SlotFactAdmin)
admin.site.register(UserResourceModifyRights, UserResourceModifyRightsAdmin)
admin.site.register(ReasonCancelSlot)
admin.site.register(SlotFactCancel, SlotFactCancelAdmin)
