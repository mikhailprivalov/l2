from django.contrib import admin

from document_management.models import (
    AddresseeGroup,
    AddresseeGroupMember,
    DocumentFieldGroups,
    DocumentFields,
    DocumentPickerFavorite,
    DocumentRecent,
    DocumentReview,
    GroupDocuments,
    PlaceSection,
    TypeSection,
    PlanIndicator,
    PlanIndicatorGroup,
    Plans,
    DocumentCase,
    DocumentCaseAccess,
    TypeCases,
    TypeDocumentCreator,
    TypeDocumentLayoutTemplate,
    TypeDocuments,
    TypeDocumentsSchema,
    UserFavoriteCase,
    UserFavoriteDocument,
)


@admin.register(GroupDocuments)
class GroupDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title")
    search_fields = ("title",)


@admin.register(TypeSection)
class TypeSectionAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "columns_count")
    search_fields = ("title",)


@admin.register(PlaceSection)
class PlaceSectionAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "columns_count", "type_section")
    search_fields = ("title",)
    list_filter = ("type_section",)


class TypeDocumentLayoutTemplateInline(admin.TabularInline):
    model = TypeDocumentLayoutTemplate
    extra = 0
    ordering = ("order", "pk")


class TypeDocumentCreatorInline(admin.TabularInline):
    model = TypeDocumentCreator
    extra = 0
    raw_id_fields = ("doctor",)


@admin.register(TypeDocuments)
class TypeDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "code", "group_document", "place_section", "layout_template")
    search_fields = ("title", "code")
    list_filter = ("group_document", "place_section")
    inlines = (TypeDocumentLayoutTemplateInline, TypeDocumentCreatorInline)


@admin.register(UserFavoriteDocument)
class UserFavoriteDocumentAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document")
    raw_id_fields = ("doctor", "document")


@admin.register(UserFavoriteCase)
class UserFavoriteCaseAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document")
    raw_id_fields = ("doctor", "document")


@admin.register(DocumentPickerFavorite)
class DocumentPickerFavoriteAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "type_document", "type_case")
    list_filter = ("doctor",)
    raw_id_fields = ("doctor", "type_document", "type_case")


@admin.register(DocumentCase)
class DocumentCaseAdmin(admin.ModelAdmin):
    list_display = ("pk", "topic", "type_case", "who_create", "created_at", "closed_at", "who_close")
    search_fields = ("topic", "comment")
    raw_id_fields = ("type_case", "who_create", "who_close")


@admin.register(DocumentCaseAccess)
class DocumentCaseAccessAdmin(admin.ModelAdmin):
    list_display = ("pk", "document_case", "doctor")
    raw_id_fields = ("document_case", "doctor")


@admin.register(TypeCases)
class TypeCasesAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "code", "default_type_document", "place_section")
    search_fields = ("title", "code")
    list_filter = ("default_type_document", "place_section")


@admin.register(Plans)
class PlansAdmin(admin.ModelAdmin):
    list_display = ("pk", "title")
    search_fields = ("title",)


@admin.register(PlanIndicatorGroup)
class PlanIndicatorGroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "plan", "title", "order")
    search_fields = ("title",)
    list_filter = ("plan",)


@admin.register(PlanIndicator)
class PlanIndicatorAdmin(admin.ModelAdmin):
    list_display = ("pk", "plan", "group", "indicator", "due_kind", "due_date", "offset_value", "offset_unit", "order")
    list_filter = ("plan", "due_kind")


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
