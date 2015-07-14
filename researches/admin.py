from django.contrib import admin

from researches.models import Researches, Tubes

admin.site.register(Researches)  # Активация формы редактирования справочника исследований в админке
admin.site.register(Tubes)  # Активация формы редактирования типов пробирок в админке
