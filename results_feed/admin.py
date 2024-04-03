from django.contrib import admin

from results_feed.models import ResultFeed


@admin.register(ResultFeed)
class ResultFeedAdmin(admin.ModelAdmin):
    list_display = ('id', 'direction', 'category', 'department_name', 'result_confirmed_at')
    list_filter = ('category',)
    search_fields = ('id', 'direction__pk', 'card__number')
    readonly_fields = ('unique_id', 'hospital', 'owner', 'individual', 'card', 'direction', 'service_names', 'department_name', 'category', 'direction_created_at', 'result_confirmed_at')
    fieldsets = (
        (
            None,
            {'fields': ('unique_id', 'hospital', 'owner', 'individual', 'card', 'direction', 'service_names', 'department_name', 'category', 'direction_created_at', 'result_confirmed_at')},
        ),
    )
