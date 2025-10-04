from django.contrib import admin
from django.contrib import messages

import integration_framework.models as models


class ResIntertationResearches(admin.ModelAdmin):
    list_display = (
        'type_integration',
        'research',
    )
    list_display_links = (
        'type_integration',
        'research',
    )
    search_fields = ('research',)
    list_filter = ('type_integration',)


class ExternalServiceAdmin(admin.ModelAdmin):
    readonly_fields = ('token',)

    list_display = (
        'title',
        'rights',
        'is_active',
    )


class ExternalServiceRights(admin.ModelAdmin):
    list_display = ('title',)


class CrieOrderAdmin(admin.ModelAdmin):
    raw_id_fields = ('local_direction',)
    list_display = (
        'local_direction',
        'system_id',
        'status',
    )
    list_display_links = (
        'local_direction',
        'system_id',
    )
    search_fields = ('local_direction',)


class EquipmentReceiveAdmin(admin.ModelAdmin):
    list_display = (
        'equipment_model',
        'napravleniye',
        'get_patient_name',
        'tag_patient_id',
        'tag_instance_id',
        'study_instance_uid_tag',

        'doc_save_link',
        'time_save_link',
        'doc_reset_link',
        'time_reset_link',
        'created_at',
        'updated_at',
    )
    list_display_links = (
        'equipment_model',
        'study_instance_uid_tag',
        'napravleniye',
    )
    list_filter = (
        'equipment_model',
        'sex',
        'doc_save_link',
        'doc_reset_link',
        'created_at',
        'updated_at',
        'time_save_link',
        'time_reset_link',
    )
    search_fields = (
        'napravleniye__pk',
        'study_instance_uid_tag',
        'family',
        'name',
        'patronymic',
        'tag_patient_id',
        'order_id',
    )
    raw_id_fields = (
        'napravleniye',
        'doc_save_link',
        'doc_reset_link',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['duplicate_equipment_receive']

    def get_patient_name(self, obj):
        return f"{obj.tag_patient_name}".strip()

    get_patient_name.short_description = 'ФИО пациента'
    get_patient_name.admin_order_field = 'family'

    def duplicate_equipment_receive(self, request, queryset):
        count = 0
        for obj in queryset:
            new_obj = models.EquipmentReceive(
                study_instance_uid_tag=obj.study_instance_uid_tag,
                napravleniye=obj.napravleniye,
                family=obj.family,
                name=obj.name,
                patronymic=obj.patronymic,
                birthday=obj.birthday,
                sex=obj.sex,
                tag_patient_id=obj.tag_patient_id,
                order_id=obj.order_id,
            )
            new_obj.save()
            count += 1

        messages.success(request, f'Успешно продублировано {count} записей')

    duplicate_equipment_receive.short_description = 'Дублировать выбранные записи'


admin.site.register(models.IntegrationResearches, ResIntertationResearches)
admin.site.register(models.EquipmentReceive, EquipmentReceiveAdmin)
admin.site.register(models.ExternalService, ExternalServiceAdmin)
admin.site.register(models.CrieOrder, CrieOrderAdmin)
admin.site.register(models.ExternalServiceRights)
