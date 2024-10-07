from django.contrib import admin

import directory.models as models


class ResDispensaryRouteSheet(admin.ModelAdmin):
    list_filter = (
        'age_client',
        'sex_client',
    )
    list_display = (
        'age_client',
        'sex_client',
        'research',
    )
    list_display_links = (
        'age_client',
        'sex_client',
        'research',
    )
    search_fields = (
        'age_client',
        'sex_client',
    )


class ResDispensaryPlan(admin.ModelAdmin):
    list_filter = (
        'diagnos',
        'speciality',
    )
    list_display = (
        'diagnos',
        'repeat',
        'research',
        'speciality_profile',
        'is_visit',
    )
    list_display_links = (
        'diagnos',
        'repeat',
        'research',
        'speciality_profile',
    )
    search_fields = ('diagnos',)

    def speciality_profile(self, obj):
        if obj.speciality:
            return obj.speciality.title
        else:
            return ""


class ResAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'internal_code',
        'pk',
        'podrazdeleniye',
    )
    list_display_links = (
        'title',
        'internal_code',
        'pk',
        'podrazdeleniye',
    )
    list_filter = ('podrazdeleniye', 'groups', 'hide', 'is_doc_refferal', 'is_paraclinic', 'is_treatment', 'is_microbiology')
    search_fields = (
        'title',
        'internal_code',
        'pk',
    )


class RefAdmin(admin.ModelAdmin):
    list_filter = ('fraction',)
    list_display = ('title', 'fraction', 'ref_m', 'ref_f', 'about')
    list_display_links = ('title',)


class RefFractions(admin.ModelAdmin):
    list_display = (
        'title',
        'research',
        'podr',
    )
    list_display_links = (
        'title',
        'research',
        'podr',
    )
    list_filter = ('research__podrazdeleniye',)
    search_fields = ('title',)
    autocomplete_fields = ('unit', 'research')

    def podr(self, obj):
        return obj.research.podrazdeleniye

    podr.short_description = "Лаборатория"
    podr.admin_order_field = 'research__podrazdeleniye'


class RefResearch(admin.ModelAdmin):
    list_display = (
        'title',
        'internal_code',
        'podr',
    )
    list_display_links = (
        'title',
        'internal_code',
        'podrazdeleniye',
    )
    list_filter = (
        'podrazdeleniye',
        'is_doc_refferal',
        'is_paraclinic',
        'is_treatment',
    )
    search_fields = (
        'title',
        'internal_code',
    )


class RefSiteType(admin.ModelAdmin):
    list_display = (
        'title',
        'site_type',
    )
    list_display_links = (
        'title',
        'site_type',
    )
    list_filter = ('site_type',)


class TitleHide(admin.ModelAdmin):
    list_display = (
        'title',
        'hide',
    )
    list_display_links = ('title',)
    list_filter = ('hide',)


class TitleFsli(admin.ModelAdmin):
    list_display = (
        'title',
        'fsli',
    )
    list_display_links = ('title',)


class HospitalServiceAdmin(admin.ModelAdmin):
    list_display = ('main_research', 'site_type', 'slave_research', 'hide')


class ResParaclinicInputField(admin.ModelAdmin):
    list_display = (
        'title',
        'group',
    )
    list_display_links = (
        'title',
        'group',
    )
    list_filter = ('group__research',)
    search_fields = (
        'id',
        'group__research__title',
    )


class ResParaclinicFieldTemplateDepartment(admin.ModelAdmin):
    list_display = (
        'paraclinic_field',
        'research',
        'department',
    )
    list_display_links = (
        'paraclinic_field',
        'research',
        'department',
    )


class ResParaclinicTemplateDepartment(admin.ModelAdmin):
    list_display = (
        'template_name',
        'department',
    )
    list_display_links = ('template_name', 'department')


class ResParaclinicInputGroups(admin.ModelAdmin):
    list_display = (
        'title',
        'pk',
        'research',
        'order',
    )
    list_display_links = (
        'title',
        'order',
    )
    list_filter = ('research',)
    search_fields = ('research__title',)


class ResHospitalService(admin.ModelAdmin):
    list_display = (
        'main_research',
        'site_type',
        'slave_research',
    )
    list_display_links = (
        'main_research',
        'slave_research',
    )
    list_filter = ('main_research',)
    search_fields = ('slave_research__title',)


class ResCulture(admin.ModelAdmin):
    list_display = (
        'title',
        'fsli',
    )
    list_display_links = ('title',)
    list_filter = ('group_culture__title',)
    search_fields = ('group_culture__title',)


class ScreeningPlanAdmin(admin.ModelAdmin):
    list_display = ('age_start_control', 'age_end_control', 'sex_client', 'research', 'period', 'hide')
    list_filter = (
        'sex_client',
        ('research', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ('research__title',)
    autocomplete_fields = ('research',)


class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_title', 'code', 'hide')
    list_filter = ('hide',)
    search_fields = ('title', 'short_title', 'code')


class ResPatientControlParam(admin.ModelAdmin):
    list_display = (
        'title',
        'code',
        'all_patient_contol',
        'order',
    )
    search_fields = ('title',)


class PhenotypeAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'fsli',
        'lis',
        'hide',
    )
    search_fields = ('title', 'fsli', 'lis')


class SetOrderResearchAdmin(admin.ModelAdmin):
    list_display = ('set_research', 'research')
    list_filter = ('set_research',)
    autocomplete_fields = ('research',)


class SetResearchAdmin(admin.ModelAdmin):
    list_display = ('title',)


class SetAuxService(admin.ModelAdmin):
    list_display = (
        'main_research',
        'aux_research',
        'hide',
    )
    list_display_links = (
        'main_research',
        'aux_research',
    )


class SetComplexService(admin.ModelAdmin):
    list_display = (
        'main_research',
        'slave_research',
        'hide',
    )
    list_display_links = (
        'main_research',
        'slave_research',
    )


class ResPatternParam(admin.ModelAdmin):
    list_display = (
        'title',
        'is_dynamic_param',
        'order',
    )
    list_display_links = (
        'title',
        'is_dynamic_param',
        'order',
    )


class ResStatisticPattern(admin.ModelAdmin):
    list_display = (
        'title',
        'hide',
    )
    list_display_links = (
        'title',
        'hide',
    )


admin.site.register(models.ResearchSite, RefSiteType)
admin.site.register(models.ResearchGroup)
admin.site.register(models.Researches, ResAdmin)
admin.site.register(models.ParaclinicInputGroups, ResParaclinicInputGroups)
admin.site.register(models.ParaclinicInputField, ResParaclinicInputField)
admin.site.register(models.ParaclinicFieldTemplateDepartment, ResParaclinicFieldTemplateDepartment)
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
admin.site.register(models.DispensaryPlan, ResDispensaryPlan)
admin.site.register(models.Culture, ResCulture)
admin.site.register(models.Antibiotic, TitleHide)
admin.site.register(models.GroupCulture)
admin.site.register(models.GroupAntibiotic)
admin.site.register(models.Localization, TitleFsli)
admin.site.register(models.ServiceLocation, TitleHide)
admin.site.register(models.HospitalService, ResHospitalService)
admin.site.register(models.ScreeningPlan, ScreeningPlanAdmin)
admin.site.register(models.Unit, UnitAdmin)
admin.site.register(models.MethodLaboratoryAnalisis)
admin.site.register(models.PatientControlParam, ResPatientControlParam)
admin.site.register(models.Phenotype, PhenotypeAdmin)
admin.site.register(models.SetResearch, SetResearchAdmin)
admin.site.register(models.SetOrderResearch, SetOrderResearchAdmin)
admin.site.register(models.AuxService, SetAuxService)
admin.site.register(models.ComplexService, SetComplexService)
admin.site.register(models.ParaclinicTemplateNameDepartment, ResParaclinicTemplateDepartment)
admin.site.register(models.PatternParam, ResPatternParam)
admin.site.register(models.StatisticPattern, ResStatisticPattern)
admin.site.register(models.StatisticPatternParamSet)
admin.site.register(models.LaboratoryMaterial)
admin.site.register(models.SubGroupDirectory)
admin.site.register(models.SubGroupPadrazdeleniye)
