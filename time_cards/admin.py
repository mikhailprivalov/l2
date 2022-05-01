from django.contrib import admin
from time_cards import models


admin.site.register(models.Posts)
admin.site.register(models.Departments)
admin.site.register(models.Persons)
admin.site.register(models.TypeWorkTime)
admin.site.register(models.Employees)
admin.site.register(models.FactTimeWork)
admin.site.register(models.Holidays)
admin.site.register(models.TabelDocuments)
