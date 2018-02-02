from django.contrib import admin

from statistics_tickets.models import ResultOfTreatment, VisitPurpose, StatisticsTicket

admin.site.register(VisitPurpose)
admin.site.register(ResultOfTreatment)
admin.site.register(StatisticsTicket)
