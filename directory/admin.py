from django.contrib import admin
import directory.models as models

class ResAdmin(admin.ModelAdmin):
    list_filter = ('subgroup', 'groups',)
    list_display = ('title', 'subgroup',)
    list_display_links = ('title', )

admin.site.register(models.ResearchGroup)
admin.site.register(models.Researches, ResAdmin)
admin.site.register(models.Absorption)
admin.site.register(models.AssignmentTemplate)
admin.site.register(models.ReleationsFT)
