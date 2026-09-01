from django.contrib import admin
import equipment.models as models


class ResEquipment(admin.ModelAdmin):
    list_filter = ('hospital',)
    list_display = (
        'title',
        'hospital',
        'ip_address',
        'manufacturer',
        'manufacturer_model_name',
        'station_name',
        'institution_name',
        'device_serial_number',
        'pacs_property',
    )
    list_display_links = ('title',)


admin.site.register(models.Equipment, ResEquipment)
