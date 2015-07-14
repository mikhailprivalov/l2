from django.contrib import admin
from podrazdeleniya.models import Podrazdeleniya


class PdnAdmin(admin.ModelAdmin):  # Форма добавления и изменения подразделений
    list_display = ('show_admin',)

    def show_admin(self, obj):  # Функция формирования строки для представления в админке
        return str(obj.pk) + " | " + str(obj)


admin.site.register(Podrazdeleniya, PdnAdmin)  # Активация формы добавления и изменения подразделений
