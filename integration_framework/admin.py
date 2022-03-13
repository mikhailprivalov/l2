from django.contrib import admin

import integration_framework.models as models


class ResIntertationResearches(admin.ModelAdmin):
    list_display = (
        'type_integration',
        'research',
    )
    list_display_links = (
        'type_integration',
        'research',
    )
    search_fields = ('research',)
    list_filter = ('type_integration',)


class ExternalServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('token',)

    list_display = (
        'title',
        'rights',
        'is_active',
    )


class ExternalServiceRights(admin.ModelAdmin):
    list_display = ('title',)


class CrieOrderAdmin(admin.ModelAdmin):
    raw_id_fields = ('local_direction',)
    list_display = (
        'local_direction',
        'system_id',
        'status',
    )
    list_display_links = (
        'local_direction',
        'system_id',
    )
    search_fields = ('local_direction',)


admin.site.register(models.IntegrationResearches, ResIntertationResearches)
admin.site.register(models.ExternalService, ExternalServiceAdmin)
admin.site.register(models.CrieOrder, CrieOrderAdmin)
admin.site.register(models.ExternalServiceRights)
