from django.contrib import admin

from .models import DoctorProfile, AssignmentTemplates, AssignmentResearches, Speciality, Position, AvailableResearchByGroup


class DocAdmin(admin.ModelAdmin):
    list_filter = ('isLDAP_user', 'podrazdeleniye', 'specialities', 'user__is_staff')
    list_display = ('fio', 'podrazdeleniye', 'isLDAP_user')
    list_display_links = ('fio',)
    search_fields = ('fio',)
    filter_horizontal = ('white_list_monitoring', 'black_list_monitoring')


admin.site.register(DoctorProfile, DocAdmin)  # Активация редактирования профилей врачей в админке
admin.site.register(AssignmentTemplates)
admin.site.register(AssignmentResearches)
admin.site.register(Speciality)
admin.site.register(Position)
admin.site.register(AvailableResearchByGroup)
