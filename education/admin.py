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


class StatementsStageAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class StatementsStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class StatementsSourceAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class ExamStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class SubjectsAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class AchievementTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class AchievementStatusAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class SpecialRightsTypeAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class SpecialRightsAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


admin.site.register(models.StatementsStage, StatementsStageAdmin)
admin.site.register(models.StatementsStatus, StatementsStatusAdmin)
admin.site.register(models.StatementsSource, StatementsSourceAdmin)
admin.site.register(models.ExamType, ExamTypeAdmin)
admin.site.register(models.ExamStatus, ExamStatusAdmin)
admin.site.register(models.Subjects, SubjectsAdmin)
admin.site.register(models.AchievementType, AchievementTypeAdmin)
admin.site.register(models.AchievementStatus, AchievementStatusAdmin)
admin.site.register(models.SpecialRightsType, SpecialRightsTypeAdmin)
admin.site.register(models.SpecialRights, SpecialRightsAdmin)
admin.site.register(models.TypeInstitutionEducation)
admin.site.register(models.InstitutionTitle, SetInstitutionTitleAdmin)
admin.site.register(models.LevelEducation)
admin.site.register(models.DocumentTypeEducation, SetDocumentTypeEducationAdmin)
