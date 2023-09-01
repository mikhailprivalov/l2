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
    list_display = ('title',)
    list_display_links = ('title',)


class ApplicationSourceEducationAdmin(admin.ModelAdmin):
    list_display = ('title',)
    list_display_links = ('title',)


class ApplicationEducationAdmin(admin.ModelAdmin):
    list_display = (
        'card',
        'speciality',
        'application_source',
    )
    list_display_links = (
        'card',
        'speciality',
        'application_source',
    )


class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'mmis_id',)
    list_display_links = ('title', 'mmis_id',)


class EntranceExamAdmin(admin.ModelAdmin):
    list_display = (
        'card',
        'type_test',
        'subjects',
        'grade',
    )
    list_display_links = (
        'card',
        'type_test',
        'subjects',
        'grade',
    )


class AchievementTypeAdmin(admin.ModelAdmin):
    list_display = (
        'short_title',
        'mmis_id',
        'grade',
        'year',
    )
    list_display_links = (
        'short_title',
        'mmis_id',
        'grade',
        'year',
    )


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
    list_display = ('card', 'right')
    list_display_links = ('card', 'right')


class FacultiesAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'mmis_id',
    )
    list_display_links = (
        'title',
        'short_title',
        'mmis_id',
    )


class EducationSpecialityAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'okso',
        'cipher',
        'mmis_id',
        'faculties_mmis_id',
        'qualification_title',
        'period_study',
        'year_start_study',
        'oo_count',
        'cn_count',
        'sn_count',
        'total_count',
    )
    list_display_links = (
        'title',
        'okso',
        'cipher',
        'mmis_id',
        'faculties_mmis_id',
        'qualification_title',
        'period_study',
        'year_start_study',
        'oo_count',
        'cn_count',
        'sn_count',
        'total_count',
    )


class SubjectsAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'short_title',
        'mmis_id',
    )
    list_display_links = (
        'title',
        'short_title',
        'mmis_id',
    )


admin.site.register(models.ApplicationSourceEducation, ApplicationSourceEducationAdmin)
admin.site.register(models.ApplicationEducation, ApplicationEducationAdmin)
admin.site.register(models.ExamType, ExamTypeAdmin)
admin.site.register(models.Subjects, SubjectsAdmin)
admin.site.register(models.EntranceExam, EntranceExamAdmin)
admin.site.register(models.AchievementType, AchievementTypeAdmin)
admin.site.register(models.Achievement)
admin.site.register(models.SpecialRightsType, SpecialRightsTypeAdmin)
admin.site.register(models.SpecialRights, SpecialRightsAdmin)
admin.site.register(models.CardSpecialRights, CardSpecialRightsAdmin)
admin.site.register(models.TypeInstitutionEducation)
admin.site.register(models.LogUpdateMMIS)
admin.site.register(models.InstitutionTitle, SetInstitutionTitleAdmin)
admin.site.register(models.LevelEducation)
admin.site.register(models.DocumentTypeEducation, SetDocumentTypeEducationAdmin)
admin.site.register(models.Faculties, FacultiesAdmin)
admin.site.register(models.EducationSpeciality, EducationSpecialityAdmin)
