from django.contrib import admin
from django.db import models as dbmodels
from django.forms import TextInput

import forms.models as models


class ResFormsList(admin.ModelAdmin):
    list_filter = ('is_active',)
    list_display = ('title', 'is_active', 'comment',)
    list_display_links = ('title',)
    search_fields = ('comment',)

    formfield_overrides = {
        dbmodels.CharField: {'widget': TextInput(attrs={'size': '50'})},
    }


admin.site.register(models.FormsList, ResFormsList)
