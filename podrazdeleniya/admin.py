from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, Chamber, Bed, PatientToBed


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
    list_display = ('pk', 'chamber', 'bed_number', 'status_bed')
    autocomplete_fields = ('chamber',)
    search_fields = ('chamber', 'bed_number')


class PatientToBedAdmin(admin.ModelAdmin):
    list_display = ('pk', '__str__', 'bed', 'entrance', 'extract')
    autocomplete_fields = ('patient',)
    search_fields = ('patient', 'bed')


admin.site.register(PatientToBed, PatientToBedAdmin)
admin.site.register(Bed, BedAdmin)
admin.site.register(Chamber, ChamberAdmin)
admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
