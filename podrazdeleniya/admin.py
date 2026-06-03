from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, Chamber, Bed, PatientToBed, PatientStationarWithoutBeds, PatientBedActionLog


class PodrazdeleniyaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'p_type', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')
    list_filter = ('hospital',)


class RoomAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')


class ChamberAdmin(admin.ModelAdmin):
    list_display = ('pk', 'podrazdelenie', 'title')
    search_fields = (
        'podrazdelenie',
        'title',
    )
    ordering = ('podrazdelenie__title',)


class BedAdmin(admin.ModelAdmin):
    list_display = ('pk', 'chamber', 'bed_number')
    autocomplete_fields = ('chamber',)
    search_fields = ('chamber', 'bed_number')


class PatientToBedAdmin(admin.ModelAdmin):
    list_display = ('pk', '__str__', 'bed', 'doctor', 'date_in', 'date_out', 'record_source')
    autocomplete_fields = ('direction',)
    search_fields = ('direction__pk',)
    list_filter = ('record_source',)


class PatientStationarWithoutBedsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'direction', 'department', 'record_source')
    list_filter = ('record_source',)


class PatientBedActionLogAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'created_at',
        'action',
        'record_source',
        'department',
        'direction',
        'bed',
        'author',
        'patient_fio_text',
    )
    list_filter = ('action', 'department', 'created_at', 'record_source')
    search_fields = ('patient_fio_text', 'direction_id', 'patient_to_bed_pk')
    readonly_fields = ('created_at',)
    ordering = ('-created_at', '-pk')


admin.site.register(PatientBedActionLog, PatientBedActionLogAdmin)
admin.site.register(PatientStationarWithoutBeds, PatientStationarWithoutBedsAdmin)
admin.site.register(PatientToBed, PatientToBedAdmin)
admin.site.register(Bed, BedAdmin)
admin.site.register(Chamber, ChamberAdmin)
admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
