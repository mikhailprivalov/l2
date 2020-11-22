from django.contrib import admin
from pharmacotherapy import models


admin.site.register(models.Drugs)
admin.site.register(models.FormRelease)
admin.site.register(models.MethodsReception)
