from django.contrib import admin
from .models import Case


class CaseAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)

admin.site.register(Case, CaseAdmin)
