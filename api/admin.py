from ajax_select.admin import AjaxSelectAdmin
from django.contrib import admin

import api.models as models


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'key', 'active')


@admin.register(models.RelationFractionASTM)
class RelationFractionASTMAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'fraction', 'signs_after_point', 'full_round')
    autocomplete_fields = ('fraction',)


admin.site.register(models.RelationCultureASTM)


@admin.register(models.Analyzer)
class AnalyzerAdmin(AjaxSelectAdmin):
    list_display = ('__str__', 'service_name', 'port', 'protocol', 'mode', 'connection_string')


@admin.register(models.ManageDoctorProfileAnalyzer)
class ManageDoctorProfileAnalyzerAdmin(AjaxSelectAdmin):
    list_display = ('__str__', 'analyzer')
