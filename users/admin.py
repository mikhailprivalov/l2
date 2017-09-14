from django.contrib import admin
from .models import DoctorProfile, AssignmentTemplates, AssignmentResearches

class DocAdmin(admin.ModelAdmin):
    list_filter = ('isLDAP_user', 'podrazileniye', 'labtype')
    list_display = ('fio', 'podrazileniye', 'isLDAP_user')
    list_display_links = ('fio', )

admin.site.register(DoctorProfile, DocAdmin)  # Активация редактирования профилей врачей в админке
admin.site.register(AssignmentTemplates)
admin.site.register(AssignmentResearches)

