from django.contrib import admin
from .models import Case


class CaseAdmin(admin.ModelAdmin):
    autocomplete_fields = ('card',)
    search_fields = ('card', 'doctor', 'case_type')


admin.site.register(Case, CaseAdmin)
