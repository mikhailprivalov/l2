from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, Chamber, Bed, PatientToBed, PatientStationarWithoutBeds


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
    autocomplete_fields = ('podrazdelenie',)
    search_fields = ('podrazdelenie', 'title')


class BedAdmin(admin.ModelAdmin):
    list_display = ('pk', 'chamber', 'bed_number')
    autocomplete_fields = ('chamber',)
    search_fields = ('chamber', 'bed_number')


class PatientToBedAdmin(admin.ModelAdmin):
    list_display = ('pk', '__str__', 'bed', 'doctor', 'date_in', 'date_out')
    autocomplete_fields = ('direction',)
    search_fields = ('direction', 'bed')


class PatientStationarWithoutBedsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'direction', 'department')


admin.site.register(PatientStationarWithoutBeds, PatientStationarWithoutBedsAdmin)
admin.site.register(PatientToBed, PatientToBedAdmin)
admin.site.register(Bed, BedAdmin)
admin.site.register(Chamber, ChamberAdmin)
admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
