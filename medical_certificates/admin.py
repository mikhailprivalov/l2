from django.contrib import admin
from medical_certificates import models

# Register your models here.

admin.site.register(models.MedicalCertificates)
admin.site.register(models.ResearchesCertificate)
