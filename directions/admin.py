from django.contrib import admin
from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya, Result, \
    FrequencyOfUseResearches, CustomResearchOrdering, RMISOrgs, RMISServiceInactive, Diagnoses

admin.site.register(IstochnikiFinansirovaniya)


@admin.register(Napravleniya)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('client',)



admin.site.register(TubesRegistration)
admin.site.register(Issledovaniya)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(RMISOrgs)
admin.site.register(RMISServiceInactive)
admin.site.register(Diagnoses)

