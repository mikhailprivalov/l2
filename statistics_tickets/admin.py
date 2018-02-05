from django.contrib import admin

from statistics_tickets.models import ResultOfTreatment, VisitPurpose, StatisticsTicket


class StatisticsTicketAdmin(admin.ModelAdmin):
    list_display = (
        'card', 'date', 'invalid_ticket', 'purpose__title', 'result__title', 'first_time', 'primary_visit',
        'dispensary_registration',
        'doctor')

    exclude = ("card ",)
    readonly_fields = ('card',)

    def purpose__title(self, obj: StatisticsTicket):
        return obj.purpose.title

    def result__title(self, obj: StatisticsTicket):
        return obj.result.title


admin.site.register(VisitPurpose)
admin.site.register(ResultOfTreatment)
admin.site.register(StatisticsTicket, StatisticsTicketAdmin)
