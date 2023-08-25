from django.contrib import admin
import education.models as models


class SetInstitutionTitleAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'type',
    )
    list_display_links = (
        'title',
        'type',
    )


class SetDocumentTypeEducationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'level_education',
    )
    list_display_links = (
        'title',
        'level_education',
    )


class FormEducationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
    )
    list_display_links = (
        'title',
    )


class StatementsStageAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class StatementsStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class StatementsSourceAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class StatementsAdmin(models.ModelAdmin):
    list_display = (
        'card',
        'speciality',
        'form',
        'source',
        'status',
        'stage',
    )
    list_display_links = (
        'card',
        'speciality',
        'form',
        'source',
        'status',
        'stage',
    )


class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class ExamStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class SubjectsAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class EntranceExamAdmin(admin.ModelAdmin):
    list_display = ('card', 'type', 'subjects', 'score', 'document_number', 'document_date', 'status')
    list_display_links = ('card', 'type', 'subjects', 'score', 'document_number', 'document_date', 'status')


class AchievementTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class AchievementStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class AchievementAdmin(admin.ModelAdmin):
    list_display = ('card', 'type', 'document_number', 'document_date', 'status')
    list_display_links = ('card', 'type', 'document_number', 'document_date', 'status')


class SpecialRightsTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class SpecialRightsAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class CardSpecialRightsAdmin(admin.ModelAdmin):
    list_display = ('title', 'right')
    list_display_links = ('title', 'right')


admin.site.register(models.FormEducation, FormEducationAdmin)
admin.site.register(models.StatementsStage, StatementsStageAdmin)
admin.site.register(models.StatementsStatus, StatementsStatusAdmin)
admin.site.register(models.StatementsSource, StatementsSourceAdmin)
admin.site.register(models.Statements, StatementsAdmin)
admin.site.register(models.ExamType, ExamTypeAdmin)
admin.site.register(models.ExamStatus, ExamStatusAdmin)
admin.site.register(models.Subjects, SubjectsAdmin)
admin.site.register(models.EntranceExam, EntranceExamAdmin)
admin.site.register(models.AchievementType, AchievementTypeAdmin)
admin.site.register(models.AchievementStatus, AchievementStatusAdmin)
admin.site.register(models.SpecialRightsType, SpecialRightsTypeAdmin)
admin.site.register(models.SpecialRights, SpecialRightsAdmin)
admin.site.register(models.CardSpecialRights, CardSpecialRightsAdmin)
admin.site.register(models.TypeInstitutionEducation)
admin.site.register(models.InstitutionTitle, SetInstitutionTitleAdmin)
admin.site.register(models.LevelEducation)
admin.site.register(models.DocumentTypeEducation, SetDocumentTypeEducationAdmin)
