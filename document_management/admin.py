from django.contrib import admin

from document_management.models import (
    AddresseeGroup,
    AddresseeGroupMember,
    DocumentFieldGroups,
    DocumentManagerLog,
    DocumentFields,
    DocumentPickerFavorite,
    DocumentRecent,
    DocumentReview,
    GroupDocuments,
    PlaceSection,
    PlaceSectionAccess,
    TypeSection,
    TypeSectionAccess,
    PlanIndicator,
    PlanIndicatorGroup,
    PlanTest,
    DouTest,
    DouTestAnswer,
    DouTestAttempt,
    DouTestQuestion,
    DouIndicator,
    DouIndicatorGroup,
    Plans,
    DocumentCase,
    DocumentCaseAccess,
    DocumentCaseLink,
    DocumentBlockLink,
    TypeCases,
    TypeDocumentCreator,
    TypeDocumentLayoutTemplate,
    TypeDocuments,
    TypeDocumentsSchema,
    UserFavoriteCase,
    UserFavoriteDocument,
    UserMyCase,
)


@admin.register(GroupDocuments)
class GroupDocumentsAdmin(admin.ModelAdmin):
    list_display = ("pk", "title")
    search_fields = ("title",)


class TypeSectionAccessInline(admin.TabularInline):
    model = TypeSectionAccess
    extra = 0
    raw_id_fields = ("doctor",)


class PlaceSectionAccessInline(admin.TabularInline):
    model = PlaceSectionAccess
    extra = 0
    raw_id_fields = ("doctor",)


@admin.register(TypeSection)
class TypeSectionAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "columns_count", "access_mode")
    search_fields = ("title",)
    inlines = (TypeSectionAccessInline,)


@admin.register(PlaceSection)
class PlaceSectionAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "columns_count", "type_section", "access_mode")
    search_fields = ("title",)
    list_filter = ("type_section", "access_mode")
    inlines = (PlaceSectionAccessInline,)


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
    list_display = ("pk", "title", "code", "group_document", "place_section", "layout_template", "monitoring", "test", "is_plan")
    raw_id_fields = ("monitoring", "test")
    search_fields = ("title", "code")
    list_filter = ("group_document", "place_section")
    inlines = (TypeDocumentLayoutTemplateInline, TypeDocumentCreatorInline)


@admin.register(UserFavoriteDocument)
class UserFavoriteDocumentAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document")
    raw_id_fields = ("doctor", "document")


@admin.register(UserMyCase)
class UserMyCaseAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document_case")
    raw_id_fields = ("doctor", "document_case")


@admin.register(UserFavoriteCase)
class UserFavoriteCaseAdmin(admin.ModelAdmin):
    list_display = ("pk", "doctor", "document", "document_case")
    raw_id_fields = ("doctor", "document", "document_case")


@admin.register(DocumentCaseLink)
class DocumentCaseLinkAdmin(admin.ModelAdmin):
    list_display = ("pk", "document", "document_case")
    raw_id_fields = ("document", "document_case")


@admin.register(DocumentBlockLink)
class DocumentBlockLinkAdmin(admin.ModelAdmin):
    list_display = ("pk", "document", "block")
    raw_id_fields = ("document", "block")


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
    list_display = ("pk", "title", "user_created", "who_create")
    raw_id_fields = ("who_create",)
    search_fields = ("title",)


class DouTestAnswerInline(admin.TabularInline):
    model = DouTestAnswer
    extra = 0
    ordering = ("order", "pk")


@admin.register(DouTest)
class DouTestAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "order_mode", "question_limit", "question_pick")
    search_fields = ("title",)


@admin.register(DouTestQuestion)
class DouTestQuestionAdmin(admin.ModelAdmin):
    list_display = ("pk", "test", "text", "order")
    search_fields = ("text",)
    list_filter = ("test",)
    inlines = (DouTestAnswerInline,)


@admin.register(DouTestAnswer)
class DouTestAnswerAdmin(admin.ModelAdmin):
    list_display = ("pk", "question", "text", "is_correct", "order")
    list_filter = ("is_correct",)


@admin.register(DouTestAttempt)
class DouTestAttemptAdmin(admin.ModelAdmin):
    list_display = ("pk", "test", "doctor", "document", "confirmed_at")
    raw_id_fields = ("test", "doctor", "document")
    list_filter = ("test",)


@admin.register(DouIndicatorGroup)
class DouIndicatorGroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "order", "who_create")
    raw_id_fields = ("who_create",)


@admin.register(DouIndicator)
class DouIndicatorAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "group", "order", "who_create")
    raw_id_fields = ("group", "who_create")


@admin.register(PlanIndicatorGroup)
class PlanIndicatorGroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "plan", "title", "order")
    search_fields = ("title",)
    list_filter = ("plan",)


@admin.register(PlanIndicator)
class PlanIndicatorAdmin(admin.ModelAdmin):
    list_display = ("pk", "plan", "group", "indicator", "due_kind", "due_date", "offset_value", "offset_unit", "order")
    list_filter = ("plan", "due_kind")


@admin.register(PlanTest)
class PlanTestAdmin(admin.ModelAdmin):
    list_display = ("pk", "plan", "group", "test", "due_kind", "due_date", "offset_value", "offset_unit", "order")
    list_filter = ("plan", "due_kind")
    raw_id_fields = ("test",)


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


@admin.register(DocumentManagerLog)
class DocumentManagerLogAdmin(admin.ModelAdmin):
    list_display = ("pk", "time", "action", "document", "document_case", "block", "object_key", "user")
    list_filter = ("action", "time")
    search_fields = ("object_key", "body", "user__fio", "user__family")
    readonly_fields = ("time", "action", "document", "document_case", "block", "object_key", "body", "user")
    raw_id_fields = ("document", "document_case", "block", "user")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
