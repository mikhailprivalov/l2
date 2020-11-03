from django.contrib import admin
from hospitals import models


class RefHospitals(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'code',
    )
    list_display_links = (
        'title',
        'short_title',
        'code',
    )
    search_fields = ('title',)


admin.site.register(models.Hospitals, RefHospitals)
