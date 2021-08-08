from django.contrib import admin
from pharmacotherapy import models


class DrugsAdmin(admin.ModelAdmin):
    search_fields = ('mnn', 'trade_name')


class FormReleaseAdmin(admin.ModelAdmin):
    search_fields = ('title',)


class MethodsReceptionAdmin(admin.ModelAdmin):
    search_fields = ('title',)


class ResProcedureList(admin.ModelAdmin):
    autocomplete_fields = (
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
    autocomplete_fields = (
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


admin.site.register(models.Drugs, DrugsAdmin)
admin.site.register(models.FormRelease, FormReleaseAdmin)
admin.site.register(models.MethodsReception, MethodsReceptionAdmin)
admin.site.register(models.ProcedureList, ResProcedureList)
admin.site.register(models.ProcedureListTimes, ResProcedureListTimes)
