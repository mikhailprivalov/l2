from django.contrib import admin
from .models import FsliRefbookTest, InstrumentalResearchRefbook, BodySiteRefbook, ArchiveMedicalDocuments, TypesMedicalDocuments



class ResArchiveMedicalDocuments(admin.ModelAdmin):
    list_display = (
        'local_uid',
        'direction',
        'message_id',
        'time_exec',
        'organization',
        'kind',
        'emdr_id',
        'registration_date',
    )

    search_fields = ('direction__pk',)



admin.site.register(FsliRefbookTest)
admin.site.register(InstrumentalResearchRefbook)
admin.site.register(BodySiteRefbook)
admin.site.register(ArchiveMedicalDocuments, ResArchiveMedicalDocuments)
admin.site.register(TypesMedicalDocuments)
