from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, Chamber, Bed, PatienToBed


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


class PatienToBedAdmin(admin.ModelAdmin):
    list_display = ('patient', 'bed', 'status')
    autocomplete_fields = ('patient',)
    search_fields = ('patient', 'bed')


admin.site.register(PatienToBed, PatienToBedAdmin)
admin.site.register(Bed, BedAdmin)
admin.site.register(Chamber, ChamberAdmin)
admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
