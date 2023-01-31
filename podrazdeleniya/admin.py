from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, Ward, Bed


class PodrazdeleniyaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'p_type', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')
    list_filter = ('hospital',)


class RoomAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')


class WardAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'department')


class BedAdmin(admin.ModelAdmin):
    list_display = ('pk', 'bed_number', 'ward', 'hide')


admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Ward, WardAdmin)
admin.site.register(Bed, BedAdmin)
