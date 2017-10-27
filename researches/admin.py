from django.contrib import admin

from researches.models import Tubes

admin.site.register(Tubes)  # Активация формы редактирования типов пробирок в админке
