from django.contrib import admin

from document_management.models import (
    AddresseeGroup,
    AddresseeGroupMember,
    DocumentFieldGroups,
    DocumentFields,
    DocumentRecent,
    DocumentReview,
    GroupDocuments,
    TypeDocumentLayoutTemplate,
    TypeDocuments,
    TypeDocumentsSchema,
)


@admin.register(GroupDocuments)
class GroupDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title")
    search_fields = ("title",)


class TypeDocumentLayoutTemplateInline(admin.TabularInline):
    model = TypeDocumentLayoutTemplate
    extra = 0
    ordering = ("order", "pk")


@admin.register(TypeDocuments)
class TypeDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "code", "group_document", "layout_template")
    search_fields = ("title", "code")
    list_filter = ("group_document",)
    inlines = (TypeDocumentLayoutTemplateInline,)


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


class AddresseeGroupMemberInline(admin.TabularInline):
    model = AddresseeGroupMember
    extra = 0
    raw_id_fields = ("doctor",)


@admin.register(AddresseeGroup)
class AddresseeGroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "who_create", "hide", "order")
    search_fields = ("title",)
    list_filter = ("hide",)
    inlines = (AddresseeGroupMemberInline,)


@admin.register(DocumentRecent)
class DocumentRecentAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document", "topic", "type_doc", "opened_at")
    search_fields = ("topic", "type_doc", "doctor__fio", "doctor__family")
    list_filter = ("opened_at",)
    raw_id_fields = ("doctor", "document")


@admin.register(DocumentReview)
class DocumentReviewAdmin(admin.ModelAdmin):
    list_display = ("pk", "document", "doctor_review", "time_review")
    search_fields = ("document__pk", "doctor_review__fio", "doctor_review__family")
    list_filter = ("time_review",)
