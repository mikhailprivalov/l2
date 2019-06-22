from django.contrib import admin
from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya, Result, \
    FrequencyOfUseResearches, CustomResearchOrdering, RMISOrgs, RMISServiceInactive, Diagnoses, TypeJob, EmployeeJob

admin.site.register(IstochnikiFinansirovaniya)


@admin.register(Napravleniya)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('client',)


@admin.register(Issledovaniya)
class IssAdmin(admin.ModelAdmin):
    raw_id_fields = ('napravleniye', 'research',)


class ResTypeJob(admin.ModelAdmin):
    list_display = ('title','value','hide',)
    list_display_links = ('title',)
    search_fields = ('title',)


class ResEmployeeJob(admin.ModelAdmin):
    list_display = ('type_job','doc_execute','count','date_job', 'time_save',)
    list_display_links = ('doc_execute',)
    search_fields = ('doc_execute__fio',)

admin.site.register(TubesRegistration)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(RMISOrgs)
admin.site.register(RMISServiceInactive)
admin.site.register(Diagnoses)
admin.site.register(TypeJob, ResTypeJob)
admin.site.register(EmployeeJob, ResEmployeeJob)

