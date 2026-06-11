from django.contrib import admin

from .models import (
    DoctorProfile,
    AssignmentTemplates,
    DoctorProfileEquipment,
    AssignmentResearches,
    Speciality,
    Position,
    AvailableResearchByGroup,
    DistrictResearchLimitAssign,
    PermissionHospitalProtocolDoctorProfile,
    DoctorProfileEmployeePosition,
    DoctorProfileEcpPosition
)


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
    filter_horizontal = (
        'white_list_monitoring',
        'black_list_monitoring',
        'disabled_fin_source',
        'room_access',
    )


class ResDistrictResearchLimitAssign(admin.ModelAdmin):
    list_display = ('district_group', 'research', 'type_period_limit', 'limit_count')
    list_display_links = ('district_group', 'research', 'type_period_limit', 'limit_count')


class ResAssignmentTemplates(admin.ModelAdmin):
    search_fields = ('title',)


class ResPosition(admin.ModelAdmin):
    list_display = ('title', 'n3_id')
    list_display_links = ('title', 'n3_id')


class ResDoctorProfileEquipment(admin.ModelAdmin):
    list_display = (
        'doctor_profile',
        'equipment',
    )
    list_display_links = (
        'doctor_profile',
        'equipment',
    )


class ResPermissionHospitalProtocolDoctorProfile(admin.ModelAdmin):
    autocomplete_fields = ('hospital', 'doctor_profile')
    list_display = ('doctor_profile', 'hospital')
    list_display_links = ('doctor_profile', 'hospital')


class ResDoctorProfileEmployeePosition(admin.ModelAdmin):
    list_display = ('doctor_profile', 'employee_position')
    list_display_links = ('doctor_profile', 'employee_position')
    search_fields = ('doctor_profile',)


class ResDoctorProfileEcpPosition(admin.ModelAdmin):
    list_display = ('doctor_profile', 'arm_type',)
    list_display_links = ('doctor_profile', 'lpu_section_name',)


admin.site.register(DoctorProfile, DocAdmin)
admin.site.register(AssignmentTemplates, ResAssignmentTemplates)
admin.site.register(AssignmentResearches)
admin.site.register(Speciality)
admin.site.register(AvailableResearchByGroup)

admin.site.register(DistrictResearchLimitAssign, ResDistrictResearchLimitAssign)
admin.site.register(Position, ResPosition)
admin.site.register(DoctorProfileEquipment, ResDoctorProfileEquipment)
admin.site.register(PermissionHospitalProtocolDoctorProfile, ResPermissionHospitalProtocolDoctorProfile)
admin.site.register(DoctorProfileEmployeePosition, ResDoctorProfileEmployeePosition)
