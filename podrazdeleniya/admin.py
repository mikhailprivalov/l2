from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room


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
    list_display = ('pk', 'title', 'hospital')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')


admin.site.register(Chamber, ChamberAdmin)
admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
