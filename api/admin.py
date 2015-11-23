from django.contrib import admin
import api.models as models
from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin

@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'key', 'active')



@admin.register(models.RelationFractionASTM)
class ApplicationAdmin(AjaxSelectAdmin):
    form = make_ajax_form(models.RelationFractionASTM, {
        'fraction': 'fraction'
    })
