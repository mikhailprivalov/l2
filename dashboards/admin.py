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


class ResDashboardChartData(admin.ModelAdmin):
    list_display = (
        'chart',
        'data_set',
        'order',
        'hide',
    )


class ResDashboardCharts(admin.ModelAdmin):
    list_display = (
        'title',
        'default_type',
        'order',
        'hide',
    )


admin.site.register(DatabaseConnectSettings, ResDatabaseConnectSettings)
admin.site.register(Dashboard)
admin.site.register(DashboardCharts, ResDashboardCharts)
admin.site.register(DashboardDataSet, ResDashboardDataSet)
admin.site.register(DashboardChartData, ResDashboardChartData)
