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


admin.site.register(models.Hospitals, RefHospitals)
