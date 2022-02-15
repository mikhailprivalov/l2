from django.contrib import admin

import plans.models as models


class ResPlanHospitalization(admin.ModelAdmin):
    list_filter = (
        'hospital_department',
    )
    list_display = (
        'hospital_department',
        'research',
        'action',
        'action',
        'work_status',
        'exec_at',
        'exec_at',
        'create_at',
    )
    list_display_links = (
        'hospital_department',
        'research',
        'action',
        'action',
        'work_status',
        'exec_at',
        'exec_at',
        'create_at',
    )
    search_fields = (
        'hospital_department',
        'research',
    )
    raw_id_fields = (
        'client',
    )


class ResLimitDatePlanHospitalization(admin.ModelAdmin):
    list_filter = (
        'hospital_department',
    )
    list_display = (
        'hospital_department',
        'research',
        'date',
        'max_count',
        'doc_who_create',
    )

    search_fields = (
        'hospital_department',
        'research',
    )

admin.site.register(models.PlanHospitalization, ResPlanHospitalization)
admin.site.register(models.LimitDatePlanHospitalization, ResLimitDatePlanHospitalization)
