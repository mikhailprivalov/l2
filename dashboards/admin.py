from django.contrib import admin
from dashboards.models import DatabaseConnectSettings


class ResDatabaseConnectSettings(admin.ModelAdmin):
    list_display = (
        'title',
        'name_database',
        'ip_address',
        'port',
    )
search_fields = ('name_database', 'ititle',)


admin.site.register(DatabaseConnectSettings, ResDatabaseConnectSettings)
