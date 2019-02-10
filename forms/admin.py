from django.contrib import admin

import forms.models as models
from django.forms import TextInput, Textarea


# Register your models here.
admin.site.register(models.FormsList)
admin.site.register(models.FormsTemplate)
