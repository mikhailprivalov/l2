from django.contrib import admin
from pharmacotherapy import models

admin.site.register(models.Drugs)
admin.site.register(models.FormRelease)
admin.site.register(models.MethodsReception)


@admin.register(models.ProcedureList)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'history',
        'diary',
        'card',
        'drug',
        'form_release',
        'method',
        'research',
        'doc_create',
        'who_cancel',
    )
    search_fields = ('pk',)
