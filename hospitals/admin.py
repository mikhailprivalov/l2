from django.contrib import admin
from hospitals import models


class RefHospitals(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'code_tfoms',
        'is_default',
    )
    list_display_links = (
        'title',
        'short_title',
        'code_tfoms',
        'is_default',
    )
    search_fields = ('title',)
    autocomplete_fields = ('client',)


class ResHospitalsGroup(admin.ModelAdmin):
    filter_horizontal = ('hospital', 'research')


class ResDisableIstochnikiFinansirovaniya(admin.ModelAdmin):
    list_display = (
        'hospital',
        'fin_source',
    )
    list_display_links = (
        'hospital',
        'fin_source',
    )
    search_fields = ('hospital__title',)
    autocomplete_fields = ('hospital',)


class RefHospitalParams(admin.ModelAdmin):
    list_display = (
        'hospital',
        'param_title',
        'param_value',
    )
    list_display_links = (
        'hospital',
        'param_title',
        'param_value',
    )
    search_fields = ('hospital__title',)
    autocomplete_fields = ('hospital',)


admin.site.register(models.Hospitals, RefHospitals)
admin.site.register(models.HospitalParams, RefHospitalParams)
admin.site.register(models.HospitalsGroup, ResHospitalsGroup)
admin.site.register(models.DisableIstochnikiFinansirovaniya, ResDisableIstochnikiFinansirovaniya)
