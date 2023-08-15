from django.contrib import admin
import education.models as models


class SetInstitutionTitleAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'type',
    )
    list_display_links = (
        'title',
        'type',
    )


admin.site.register(models.TypeInstitutionEducation)
admin.site.register(models.InstitutionTitle, SetInstitutionTitleAdmin)
admin.site.register(models.LevelEducation)
admin.site.register(models.DocumentTypeEducation)
