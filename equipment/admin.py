from django.contrib import admin
import equipment.models as models


class ResEquipment(admin.ModelAdmin):
    list_filter = ('hospital',)
    list_display = (
        'title',
        'hospital',
    )
    list_display_links = ('title',)


admin.site.register(models.Equipment, ResEquipment)
