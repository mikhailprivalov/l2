from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya, Room, WardDepartment, BedDepartment


class PodrazdeleniyaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'p_type', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')
    list_filter = ('hospital',)


class RoomAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'hospital', 'hide')
    autocomplete_fields = ('hospital',)
    search_fields = ('title', 'hospital')


class WardDepartmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'department')


class BedDepartmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ward', 'bed_number')


admin.site.register(Podrazdeleniya, PodrazdeleniyaAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(WardDepartment, WardDepartmentAdmin)
admin.site.register(BedDepartment, BedDepartmentAdmin)
