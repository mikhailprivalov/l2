from django.contrib import admin

import directory.models as models


class ResDispensaryRouteSheet(admin.ModelAdmin):
    list_filter = ('age_client', 'sex_client',)
    list_display = ('age_client', 'sex_client', 'research',)
    list_display_links = ('age_client', 'sex_client', 'research',)
    search_fields = ('age_client', 'sex_client',)


class ResAdmin(admin.ModelAdmin):
    list_display = ('title', 'internal_code', 'pk', 'podrazdeleniye',)
    list_display_links = ('title', 'internal_code', 'pk', 'podrazdeleniye',)
    list_filter = ('podrazdeleniye', 'groups', 'hide', 'is_doc_refferal', 'is_paraclinic', 'is_treatment',)
    search_fields = ('title', 'internal_code', 'pk',)


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


class HospitalServiceAdmin(admin.ModelAdmin):
    list_display = ('main_research', 'site_type', 'slave_research', 'hide')


class ResParaclinicInputField(admin.ModelAdmin):
    list_display = ('title', 'group',)
    list_display_links = ('title', 'group',)
    list_filter = ('group',)
    search_fields = ('group__pk',)


class ResParaclinicInputGroups(admin.ModelAdmin):
    list_display = ('title', 'pk', 'research',)
    list_display_links = ('title',)
    list_filter = ('research',)
    search_fields = ('research__title',)


class ResHospitalService(admin.ModelAdmin):
    list_display = ('main_research', 'site_type', 'slave_research',)
    list_display_links = ('main_research', 'slave_research',)
    list_filter = ('main_research',)
    search_fields = ('slave_research__title',)


class ResCulture(admin.ModelAdmin):
    list_display = ('title', 'fsli',)
    list_display_links = ('title',)
    list_filter = ('group_culture__title',)
    search_fields = ('group_culture__title',)


class ResAntibioticSets(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)
    list_filter = ('title', 'antibiotics__title',)
    search_fields = ('antibiotics__title',)


admin.site.register(models.ResearchSite, RefSiteType)
admin.site.register(models.ResearchGroup)
admin.site.register(models.Researches, ResAdmin)
admin.site.register(models.ParaclinicInputGroups, ResParaclinicInputGroups)
admin.site.register(models.ParaclinicInputField, ResParaclinicInputField)
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
admin.site.register(models.Culture, ResCulture)
admin.site.register(models.Antibiotic, TitleHide)
admin.site.register(models.GroupCulture)
admin.site.register(models.GroupAntibiotic)
admin.site.register(models.Localization, TitleFsli)
admin.site.register(models.ServiceLocation, TitleHide)
admin.site.register(models.HospitalService, ResHospitalService)
admin.site.register(models.AntibioticSets, ResAntibioticSets)
