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


class DrugsTemplatesAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'doc_create',
        'time_create',
        'who_update',
        'time_update'
    )
    list_filter = ('time_create', 'time_update')
    search_fields = ('pk',)


class DrugsTemplatesDepartmentsAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'department',
    )
    list_filter = ('template',)
    search_fields = ('pk', 'template')

class DrugsTemplatesRowsAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'drug',
        'form_release',
        'method',
        'dosage',
        'units',
        'days_count',
        'step',
        'comment',
    )
    list_filter = ('template',)
    search_fields = ('pk', 'template',)


class DrugsTemplatesRowsTimesAdmin(admin.ModelAdmin):
    list_display = (
        'row',
        'times_medication',
    )
    list_filter = ('row',)
    search_fields = ('pk', 'row',)


admin.site.register(models.Drugs, DrugsAdmin)
admin.site.register(models.FormRelease, FormReleaseAdmin)
admin.site.register(models.MethodsReception, MethodsReceptionAdmin)
admin.site.register(models.ProcedureList, ResProcedureList)
admin.site.register(models.ProcedureListTimes, ResProcedureListTimes)
admin.site.register(models.DrugsTemplate, DrugsTemplatesAdmin)
admin.site.register(models.DrugsTemplatesRow, DrugsTemplatesRowsAdmin)
admin.site.register(models.DrugsTemplatesRowsTime, DrugsTemplatesRowsTimesAdmin)
admin.site.register(models.DrugsTemplatesDepartment, DrugsTemplatesDepartmentsAdmin)
