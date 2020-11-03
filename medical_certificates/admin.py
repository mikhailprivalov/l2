from django.contrib import admin
from medical_certificates import models


class RefResearchesCertificates(admin.ModelAdmin):
    list_display = (
        'cert_research',
        'cert_form',
        'certificate_form',
    )
    list_display_links = (
        'cert_research',
        'cert_form',
    )
    search_fields = ('research__title',)

    def cert_research(self, obj):
        return obj.research.title

    def cert_form(self, obj):
        return obj.medical_certificate.title

    def certificate_form(self, obj):
        return obj.medical_certificate.certificate_form


admin.site.register(models.MedicalCertificates)
admin.site.register(models.ResearchesCertificate, RefResearchesCertificates)
