from django.contrib import admin

from statistics_tickets.models import ResultOfTreatment, VisitPurpose

admin.site.register(VisitPurpose)
admin.site.register(ResultOfTreatment)
