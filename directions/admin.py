from django.contrib import admin
from .models import IstochnikiFinansirovaniya, Napravleniya, TubesRegistration, Issledovaniya, Result, \
    FrequencyOfUseResearches, CustomResearchOrdering, RMISOrgs, RMISServiceInactive, Diagnoses, PriceName, PriceCoast

admin.site.register(IstochnikiFinansirovaniya)


@admin.register(Napravleniya)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('client',)


class ResPriceCoast(admin.ModelAdmin):
    list_filter = ('price_name','price_name__active_status',)
    list_display = ('price_name','research', 'coast','status',)
    # fields = [('form_name',), ('section_name','is_print_section',),'template_text']
    list_display_links = ('price_name','research', 'coast',)


    def status(self, obj):
        return obj.price_name.status()

    status.short_description = 'Status'


admin.site.register(TubesRegistration)
admin.site.register(Issledovaniya)
admin.site.register(Result)
admin.site.register(FrequencyOfUseResearches)
admin.site.register(CustomResearchOrdering)
admin.site.register(RMISOrgs)
admin.site.register(RMISServiceInactive)
admin.site.register(Diagnoses)
admin.site.register(PriceName)
admin.site.register(PriceCoast, ResPriceCoast)
