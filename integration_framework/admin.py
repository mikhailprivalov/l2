from django.contrib import admin

import integration_framework.models as models


class ResIntertationResearches(admin.ModelAdmin):
    list_display = ('type_integration', 'research',)
    list_display_links = ('type_integration', 'research',)
    search_fields = ('research',)
    list_filter = ('type_integration',)


admin.site.register(models.IntegrationResearches, ResIntertationResearches)
