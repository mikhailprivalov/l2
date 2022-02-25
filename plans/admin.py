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
        'plan_client',
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
        'plan_client',
    )
    search_fields = (
        'hospital_department',
        'research',
    )
    raw_id_fields = (
        'client',
    )

    def plan_client(self, obj):
        if obj:
            return obj.client.get_fio_w_card()
        else:
            return ""


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


class ResPlanHospitalizationFiles(admin.ModelAdmin):
    list_display = (
        'created_at',
        'uploaded_file',
        'plan_research',
        'plan_client'
    )

    list_display_links = (
        'created_at',
        'uploaded_file',
        'plan_research',
        'plan_client'
    )
    def plan_research(self, obj):
        if obj.plan:
            return obj.plan.research.title
        else:
            return ""

    def plan_client(self, obj):
        if obj.plan:
            return obj.plan.client.get_fio_w_card()
        else:
            return ""

admin.site.register(models.PlanHospitalization, ResPlanHospitalization)
admin.site.register(models.LimitDatePlanHospitalization, ResLimitDatePlanHospitalization)
admin.site.register(models.PlanHospitalizationFiles, ResPlanHospitalizationFiles)
