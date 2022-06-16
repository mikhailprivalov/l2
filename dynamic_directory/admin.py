from django.contrib import admin

import dynamic_directory.models as models


class DirectoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'root_directory', 'hide')
    search_fields = ('title', 'code')


class DirectoryFieldAdmin(admin.ModelAdmin):
    list_display = ('directory', 'title', 'field_type', 'hide')
    search_fields = ('title',)


class DirectoryRecordAdmin(admin.ModelAdmin):
    list_display = ('directory', 'title', 'code', 'last_version', 'hide')
    search_fields = ('title',)


class DirectoryRecordVersionAdmin(admin.ModelAdmin):
    list_display = ('record', 'version')


class DirectoryRecordValueAdmin(admin.ModelAdmin):
    list_display = ('record_version', 'field', 'text_value')


admin.site.register(models.Directory, DirectoryAdmin)
admin.site.register(models.DirectoryField, DirectoryFieldAdmin)
admin.site.register(models.DirectoryRecord, DirectoryRecordAdmin)
admin.site.register(models.DirectoryRecordVersion, DirectoryRecordVersionAdmin)
admin.site.register(models.DirectoryRecordValue, DirectoryRecordValueAdmin)
