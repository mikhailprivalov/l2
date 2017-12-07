from django.contrib import admin
import api.models as models
from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'key', 'active')


admin.site.register(models.RelationFractionASTM)


@admin.register(models.Analyzer)
class ApplicationAdmin(AjaxSelectAdmin):
    list_display = ('__str__', 'protocol', 'mode', 'connection_string')
