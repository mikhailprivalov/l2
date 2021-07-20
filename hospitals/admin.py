from django.contrib import admin
from hospitals import models


class RefHospitals(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'code_tfoms',
    )
    list_display_links = (
        'title',
        'short_title',
        'code_tfoms',
    )
    search_fields = ('title',)
    raw_id_fields = ('client',)


admin.site.register(models.Hospitals, RefHospitals)
admin.site.register(models.HospitalsGroup)
