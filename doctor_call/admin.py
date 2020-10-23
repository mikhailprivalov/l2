from django.contrib import admin
from .models import DoctorCall


class ResDoctorCall(admin.ModelAdmin):
    raw_id_fields = ('client',)
    list_display = ('client', 'exec_at', 'create_at', 'research')
    list_display_links = ('client', 'exec_at', 'create_at')
    search_fields = ('research__title',)

admin.site.register(DoctorCall, ResDoctorCall)
