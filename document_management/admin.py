from django.contrib import admin

from document_management.models import DocumentFieldGroups, DocumentFields, GroupDocuments, TypeDocuments, TypeDocumentsSchema


@admin.register(GroupDocuments)
class GroupDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title")
    search_fields = ("title",)


@admin.register(TypeDocuments)
class TypeDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "code", "group_document", "layout_template")
    search_fields = ("title", "code")
    list_filter = ("group_document",)


@admin.register(DocumentFieldGroups)
class DocumentFieldGroupsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "type_document", "order", "hide")
    list_filter = ("type_document",)


@admin.register(DocumentFields)
class DocumentFieldsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "type_document", "group", "field_type", "order", "hide")
    list_filter = ("type_document", "field_type")


@admin.register(TypeDocumentsSchema)
class TypeDocumentsSchemaAdmin(admin.ModelAdmin):
    list_display = ("pk", "type_document", "version", "created_at")
    search_fields = ("version", "type_document__title")
    list_filter = ("type_document",)
    readonly_fields = ("version", "created_at", "schema")
