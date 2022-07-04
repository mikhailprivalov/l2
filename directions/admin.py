from django.contrib import admin

from .models import (
    IstochnikiFinansirovaniya,
    Napravleniya,
    TubesRegistration,
    Issledovaniya,
    Result,
    FrequencyOfUseResearches,
    CustomResearchOrdering,
    RMISOrgs,
    RMISServiceInactive,
    Diagnoses,
    TypeJob,
    EmployeeJob,
    KeyValue,
    PersonContract,
    ExternalOrganization,
    DirectionsHistory,
    MonitoringResult,
    Dashboard,
    DashboardCharts,
    DashboardChartFields,
    MonitoringSumFieldByDay,
    MonitoringSumFieldTotal,
    NumberGenerator,
    DirectionDocument,
    DocumentSign,
    AdditionNapravleniya,
    IssledovaniyaFiles,
    IssledovaniyaResultLaborant,
    MicrobiologyResultCulture,
    MicrobiologyResultPhenotype,
)

admin.site.register(IstochnikiFinansirovaniya)


@admin.register(Napravleniya)
class NapravleniyaAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'client',
        'case',
        'parent',
        'parent_auto_gen',
        'parent_slave_hosp',
    )
    search_fields = (
        'pk',
        'client',
    )


@admin.register(DirectionDocument)
class DirectionDocumentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('direction',)
    search_fields = ('direction',)


@admin.register(DocumentSign)
class DocumentSignAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'document',
        'executor',
    )
    search_fields = (
        'document',
        'executor',
    )


@admin.register(Issledovaniya)
class IssAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'napravleniye',
        'research',
        'parent',
    )
    raw_id_fields = ('tubes',)
    search_fields = ('napravleniye__pk',)


@admin.register(NumberGenerator)
class NumberGeneratorAdmin(admin.ModelAdmin):
    autocomplete_fields = ('hospital',)
    search_fields = ('hospital', 'year', 'key')
    list_display = (
        'hospital',
        'key',
        'year',
        'is_active',
        'start',
        'end',
        'last',
    )


class ResTypeJob(admin.ModelAdmin):
    list_display = (
        'title',
        'value',
        'hide',
    )
    list_display_links = ('title',)
    search_fields = ('title',)


class ResEmployeeJob(admin.ModelAdmin):
    list_display = (
        'type_job',
        'doc_execute',
        'count',
        'date_job',
        'time_save',
    )
    list_display_links = ('doc_execute',)
    search_fields = ('doc_execute__fio',)


class ResKeyValue(admin.ModelAdmin):
    list_display = (
        'key',
        'value',
    )
    list_display_links = ('value',)
    search_fields = ('value',)


class ResDiagnoses(admin.ModelAdmin):
    search_fields = ('code',)
    list_filter = ('d_type',)


class ResPersonContract(admin.ModelAdmin):
    list_display = (
        'num_contract',
        'sum_contract',
        'patient_data',
        'patient_card',
        'dir_list',
        'protect_code',
    )
    raw_id_fields = (
        'patient_card',
        'payer_card',
        'agent_card',
    )
    search_fields = ('num_contract',)


class ResDirectionsHistory(admin.ModelAdmin):
    autocomplete_fields = (
        'direction',
        'old_card',
        'new_card',
    )
    list_display = (
        'direction_num',
        'old_fio_born',
        'new_fio_born',
        'date_change',
        'who_change',
    )
    search_fields = ('direction__pk',)

    def direction_num(self, obj):
        if obj.direction:
            return obj.direction.pk
        else:
            return ""


class ResMonitoringResult(admin.ModelAdmin):
    list_display = (
        'napravleniye',
        'hospital',
        'type_period',
        'value_aggregate',
    )
    search_fields = ('napravleniye__pk',)

    autocomplete_fields = (
        'napravleniye',
        'issledovaniye',
    )


class ResDashboardChartFields(admin.ModelAdmin):
    list_display = (
        'charts',
        'field',
        'title_for_field',
    )
    search_fields = ('charts__title',)


class ResDashboardCharts(admin.ModelAdmin):
    list_display = (
        'title',
        'dashboard',
    )

    list_filter = ('dashboard__title',)
    search_fields = ('title',)


class ResAdditionNapravleniya(admin.ModelAdmin):
    list_display = (
        'target_direction',
        'addition_direction',
    )
    search_fields = (
        'target_direction__pk',
        'addition_direction__pk',
    )


class ResIssledovaniyaFiles(admin.ModelAdmin):
    list_display = (
        'issledovaniye',
        'uploaded_file',
        'created_at',
    )
    search_fields = ('issledovaniye__pk',)


class ResIssledovaniyaResultLaborant(admin.ModelAdmin):
    list_display = (
        'issledovaniye',
        'napravleniye',
        'field',
    )
    search_fields = ('napravleniye__pk',)


class MicrobiologyResultCultureAdmin(admin.ModelAdmin):
    autocomplete_fields = ('issledovaniye',)
    list_display = (
        'issledovaniye',
        'culture',
    )
    search_fields = ('issledovaniye', 'culture__title')


class MicrobiologyResultPhenotypeAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'result_culture',
        'phenotype',
    )
    list_display = (
        'result_culture',
        'phenotype',
    )
    search_fields = ('phenotype__title',)


admin.site.register(TubesRegistration)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(ExternalOrganization)
admin.site.register(RMISOrgs)
admin.site.register(RMISServiceInactive)
admin.site.register(Diagnoses, ResDiagnoses)
admin.site.register(TypeJob, ResTypeJob)
admin.site.register(EmployeeJob, ResEmployeeJob)
admin.site.register(KeyValue, ResKeyValue)
admin.site.register(PersonContract, ResPersonContract)
admin.site.register(DirectionsHistory, ResDirectionsHistory)
admin.site.register(MonitoringResult, ResMonitoringResult)
admin.site.register(Dashboard)
admin.site.register(DashboardCharts, ResDashboardCharts)
admin.site.register(DashboardChartFields, ResDashboardChartFields)
admin.site.register(MonitoringSumFieldByDay)
admin.site.register(MonitoringSumFieldTotal)
admin.site.register(AdditionNapravleniya, ResAdditionNapravleniya)
admin.site.register(IssledovaniyaFiles, ResIssledovaniyaFiles)
admin.site.register(IssledovaniyaResultLaborant, ResIssledovaniyaResultLaborant)
admin.site.register(MicrobiologyResultCulture, MicrobiologyResultCultureAdmin)
admin.site.register(MicrobiologyResultPhenotype, MicrobiologyResultPhenotypeAdmin)
