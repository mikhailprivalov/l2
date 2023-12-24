from django.contrib import admin
from .models import FsliRefbookTest, InstrumentalResearchRefbook, BodySiteRefbook, ArchiveMedicalDocuments, TypesMedicalDocuments, CdaFields, ProfessionsWorkersPositionsRefbook


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


class ResCdaFields(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
        'is_doc_refferal',
        'is_treatment',
        'is_form',
    )
    list_filter = (
        'is_doc_refferal',
        'is_treatment',
        'is_form',
    )
    search_fields = (
        'code',
        'title',
    )


class ResProfessionsWorkersPositionsRefbook(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
    )
    search_fields = ('title',)


admin.site.register(FsliRefbookTest)
admin.site.register(InstrumentalResearchRefbook)
admin.site.register(BodySiteRefbook)
admin.site.register(ArchiveMedicalDocuments, ResArchiveMedicalDocuments)
admin.site.register(TypesMedicalDocuments)
admin.site.register(CdaFields, ResCdaFields)
admin.site.register(ProfessionsWorkersPositionsRefbook, ResProfessionsWorkersPositionsRefbook)
