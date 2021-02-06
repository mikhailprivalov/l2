from django.contrib import admin
from pharmacotherapy import models

admin.site.register(models.Drugs)
admin.site.register(models.FormRelease)
admin.site.register(models.MethodsReception)


# admin.site.register(models.ProcedureListTimes)


class ResProcedureList(admin.ModelAdmin):
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
    list_display = (
        'history',
        'card',
    )

    search_fields = ('pk',)


class ResProcedureListTimes(admin.ModelAdmin):
    raw_id_fields = (
        'prescription',
        'executor',
        'who_cancel',
    )
    list_display = (
        'prescription',
        'who_cancel',
        'executor',
    )

    search_fields = ('pk',)


admin.site.register(models.ProcedureList, ResProcedureList)
admin.site.register(models.ProcedureListTimes, ResProcedureListTimes)
