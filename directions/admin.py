from django.contrib import admin
from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya, Result, \
    FrequencyOfUseResearches, CustomResearchOrdering, RMISOrgs

admin.site.register(IstochnikiFinansirovaniya)  # Активация формы добавления и изменения источников финансировнаия
admin.site.register(Napravleniya)
admin.site.register(TubesRegistration)
admin.site.register(Issledovaniya)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(RMISOrgs)
