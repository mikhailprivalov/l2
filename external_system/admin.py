from django.contrib import admin

from .models import FsliRefbookTest, InstrumentalResearchRefbook, BodySiteRefbook, ArchiveMedicalDocuments, TypesMedicalDocuments

admin.site.register(FsliRefbookTest)
admin.site.register(InstrumentalResearchRefbook)
admin.site.register(BodySiteRefbook)
admin.site.register(ArchiveMedicalDocuments)
admin.site.register(TypesMedicalDocuments)
