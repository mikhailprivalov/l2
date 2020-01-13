from django.contrib import admin

from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya, Result, \
    FrequencyOfUseResearches, CustomResearchOrdering, RMISOrgs, RMISServiceInactive, Diagnoses, TypeJob, EmployeeJob, \
    KeyValue, PersonContract

admin.site.register(IstochnikiFinansirovaniya)


@admin.register(Napravleniya)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('client',)


@admin.register(Issledovaniya)
class IssAdmin(admin.ModelAdmin):
    raw_id_fields = ('napravleniye', 'research',)


class ResTypeJob(admin.ModelAdmin):
    list_display = ('title', 'value', 'hide',)
    list_display_links = ('title',)
    search_fields = ('title',)


class ResEmployeeJob(admin.ModelAdmin):
    list_display = ('type_job', 'doc_execute', 'count', 'date_job', 'time_save',)
    list_display_links = ('doc_execute',)
    search_fields = ('doc_execute__fio',)


class ResKeyValue(admin.ModelAdmin):
    list_display = ('key', 'value',)
    list_display_links = ('value',)
    search_fields = ('value',)


class ResDiagnoses(admin.ModelAdmin):
    search_fields = ('code',)


class ResPersonContract(admin.ModelAdmin):
    list_display = ('num_contract', 'sum_contract', 'patient_data', 'patient_card', 'dir_list', 'protect_code',)
    search_fields = ('num_contract',)


admin.site.register(TubesRegistration)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(RMISOrgs)
admin.site.register(RMISServiceInactive)
admin.site.register(Diagnoses, ResDiagnoses)
admin.site.register(TypeJob, ResTypeJob)
admin.site.register(EmployeeJob, ResEmployeeJob)
admin.site.register(KeyValue, ResKeyValue)
admin.site.register(PersonContract, ResPersonContract)
