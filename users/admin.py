from django.contrib import admin
from .models import DoctorProfile, AssignmentTemplates, AssignmentResearches, Speciality


class DocAdmin(admin.ModelAdmin):
    list_filter = ('isLDAP_user', 'podrazdeleniye', 'specialities', 'user__is_staff')
    list_display = ('fio', 'podrazdeleniye', 'isLDAP_user')
    list_display_links = ('fio',)


admin.site.register(DoctorProfile, DocAdmin)  # Активация редактирования профилей врачей в админке
admin.site.register(AssignmentTemplates)
admin.site.register(AssignmentResearches)
admin.site.register(Speciality)
