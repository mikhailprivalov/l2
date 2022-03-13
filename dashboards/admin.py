from django.contrib import admin
from dashboards.models import DatabaseConnectSettings, Dashboard, DashboardCharts, DashboardDataSet, DashboardChartData


class ResDatabaseConnectSettings(admin.ModelAdmin):
    list_display = (
        'title',
        'database',
        'ip_address',
        'port',
    )
    search_fields = (
        'name_database',
        'ititle',
    )


class ResDashboardDataSet(admin.ModelAdmin):
    list_display = (
        'title',
        'connect',
        'sql_columns_settings',
    )


admin.site.register(DatabaseConnectSettings, ResDatabaseConnectSettings)
admin.site.register(Dashboard)
admin.site.register(DashboardCharts)
admin.site.register(DashboardDataSet)
admin.site.register(DashboardChartData)
