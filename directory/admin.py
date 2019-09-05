from django.contrib import admin
import directory.models as models
from django.forms import TextInput, Textarea
from django.db import models as dbmodels


class RouteSheetInline(admin.TabularInline):
    model = models.RouteSheet
    extra = 0
    formfield_overrides = {
        dbmodels.CharField: {'widget': TextInput(attrs={'size': '10'})},
        dbmodels.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 55})},
    }

class ResRouteSheet(admin.ModelAdmin):
    list_filter = ('name_route_sheet',)
    list_display = ('name_route_sheet', 'research', 'work_time', 'cabinet', 'comment',)
    fields = ['name_route_sheet', 'research', ('work_time', 'cabinet', 'comment')]
    list_display_links = ('name_route_sheet',)

    formfield_overrides = {
        dbmodels.CharField: {'widget': TextInput(attrs={'size': '25'})},
        dbmodels.TextField: {'widget': Textarea(attrs={'rows': 2, 'cols': 55})},
    }


class ResNameRouteSheet(admin.ModelAdmin):
    list_display = ('title', 'static_text',)
    list_display_links = ('title',)
    inlines = [RouteSheetInline]


class ResAdmin(admin.ModelAdmin):
    list_display = ('title', 'internal_code', 'pk', 'podrazdeleniye',)
    list_display_links = ('title', 'internal_code', 'pk', 'podrazdeleniye',)
    list_filter = ('podrazdeleniye','groups', 'hide', 'is_doc_refferal', 'is_paraclinic', 'is_treatment',)
    search_fields = ('title', 'internal_code','pk',)


class RefAdmin(admin.ModelAdmin):
    list_filter = ('fraction',)
    list_display = ('title', 'fraction', 'ref_m', 'ref_f', 'about')
    list_display_links = ('title',)


class RefFractions(admin.ModelAdmin):
    list_display = ('title', 'research', 'podr',)
    list_display_links = ('title', 'research', 'podr',)
    list_filter = ('research__podrazdeleniye',)
    search_fields = ('title',)
    def podr(self, obj):
        return obj.research.podrazdeleniye

    podr.short_description = "Лаборатория"
    podr.admin_order_field = 'research__podrazdeleniye'

class RefResearch(admin.ModelAdmin):
    list_display = ('title', 'internal_code', 'podr',)
    list_display_links = ('title', 'internal_code', 'podrazdeleniye',)
    list_filter = ('podrazdeleniye', 'is_doc_refferal', 'is_paraclinic', 'is_treatment',)
    search_fields = ('title', 'internal_code',)


class RefSiteType(admin.ModelAdmin):
    list_display = ('title', 'site_type',)
    list_display_links = ('title', 'site_type',)
    list_filter = ('site_type',)


class TitleHide(admin.ModelAdmin):
    list_display = ('title', 'hide',)
    list_display_links = ('title',)
    list_filter = ('hide',)


admin.site.register(models.ResearchSite, RefSiteType)
admin.site.register(models.ResearchGroup)
admin.site.register(models.Researches, ResAdmin)
admin.site.register(models.ParaclinicInputGroups)
admin.site.register(models.ParaclinicInputField)
admin.site.register(models.References, RefAdmin)
admin.site.register(models.ResultVariants)
admin.site.register(models.MaterialVariants)
admin.site.register(models.Fractions, RefFractions)
admin.site.register(models.Absorption)
admin.site.register(models.ReleationsFT)
admin.site.register(models.AutoAdd)
admin.site.register(models.ParaclinicTemplateName)
admin.site.register(models.ParaclinicTemplateField)

admin.site.register(models.RouteSheet, ResRouteSheet)
admin.site.register(models.NameRouteSheet, ResNameRouteSheet)

admin.site.register(models.Culture, TitleHide)
admin.site.register(models.Antibiotic, TitleHide)
