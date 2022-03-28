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
    list_display_links = (
        'title',
        'connect',
        'sql_columns_settings',
    )


class ResDashboardChartData(admin.ModelAdmin):
    list_display = (
        'dashboard_title',
        'chart',
        'data_set',
        'order',
        'hide',
    )
    list_display_links = (
        'dashboard_title',
        'chart',
        'data_set',
        'order',
        'hide',
    )

    def dashboard_title(self, obj):
        if obj.chart.dashboard:
            return obj.chart.dashboard.title
        else:
            return ""


class ResDashboardCharts(admin.ModelAdmin):
    list_display = (
        'dashboard',
        'title',
        'default_type',
        'order',
        'hide',
    )
    list_display_links = (
        'dashboard',
        'title',
        'default_type',
        'order',
        'hide',
    )


class ResDashboard(admin.ModelAdmin):
    list_display = (
        'title',
        'order',
        'interval_reload_seconds',
        'hide',
    )
    list_display_links = (
        'title',
        'order',
        'interval_reload_seconds',
        'hide',
    )


admin.site.register(DatabaseConnectSettings, ResDatabaseConnectSettings)
admin.site.register(Dashboard, ResDashboard)
admin.site.register(DashboardCharts, ResDashboardCharts)
admin.site.register(DashboardDataSet, ResDashboardDataSet)
admin.site.register(DashboardChartData, ResDashboardChartData)
