from django.contrib import admin

from .models import DoctorProfile, AssignmentTemplates, AssignmentResearches, Speciality, Position, AvailableResearchByGroup, DistrictResearchLimitAssign


class DocAdmin(admin.ModelAdmin):
    list_filter = (
        'podrazdeleniye',
        'specialities',
        'user__is_staff',
    )
    list_display = (
        'fio',
        'podrazdeleniye',
    )
    list_display_links = ('fio',)
    search_fields = ('fio',)
    filter_horizontal = ('white_list_monitoring', 'black_list_monitoring', 'disabled_fin_source', 'room_access',)


class ResDistrictResearchLimitAssign(admin.ModelAdmin):
    list_display = ('district_group', 'research', 'type_period_limit', 'limit_count')
    list_display_links = ('district_group', 'research', 'type_period_limit', 'limit_count')


class ResAssignmentTemplates(admin.ModelAdmin):
    search_fields = ('title',)


class ResPosition(admin.ModelAdmin):
    list_display = ('title', 'n3_id',)
    list_display_links = ('title', 'n3_id',)


admin.site.register(DoctorProfile, DocAdmin)
admin.site.register(AssignmentTemplates, ResAssignmentTemplates)
admin.site.register(AssignmentResearches)
admin.site.register(Speciality)
admin.site.register(AvailableResearchByGroup)

admin.site.register(DistrictResearchLimitAssign, ResDistrictResearchLimitAssign)
admin.site.register(Position, ResPosition)
