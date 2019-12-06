from django.contrib import admin
import directory.models as models
from django.forms import TextInput, Textarea
from django.db import models as dbmodels

class ResDispensaryRouteSheet(admin.ModelAdmin):
    list_filter = ('age_client', 'sex_client',)
    list_display = ('age_client', 'sex_client', 'research',)
    list_display_links = ('age_client', 'sex_client', 'research',)
    search_fields = ('age_client', 'sex_client',)


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


class TitleFsli(admin.ModelAdmin):
    list_display = ('title', 'fsli',)
    list_display_links = ('title',)


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
admin.site.register(models.DirectionsGroup)

admin.site.register(models.DispensaryRouteSheet, ResDispensaryRouteSheet)

admin.site.register(models.Culture, TitleHide)
admin.site.register(models.Antibiotic, TitleHide)

admin.site.register(models.Localization, TitleFsli)
admin.site.register(models.ServiceLocation, TitleHide)
admin.site.register(models.HospitalResearch)
admin.site.register(models.HospitalSite)