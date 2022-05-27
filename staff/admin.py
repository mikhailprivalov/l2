from django.contrib import admin
from staff import models


class ResPersons(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'snils',)
    list_display_links = ('last_name', 'first_name', 'patronymic', 'snils',)
    search_fields = (
        'snils',
    )
    list_display_links = (
        'last_name',
        'first_name',
        'patronymic',
        'snils',
    )
    search_fields = ('snils',)
    list_display_links = (
        'last_name',
        'first_name',
        'patronymic',
        'snils',
    )
    search_fields = ('snils',)
    list_display_links = (
        'last_name',
        'first_name',
        'patronymic',
        'snils',
    )
    search_fields = ('snils',)
    list_display_links = (

class ResEmployees(admin.ModelAdmin):
    list_display = ('tabel_number', 'person', 'department', 'tabel_number',)
    list_display_links = ('tabel_number', 'person', 'department', 'tabel_number',)
    search_fields = (
        'tabel_number',
    )
    list_display_links = (
        'tabel_number',
        'person',
        'department',
        'tabel_number',
    )
    search_fields = ('tabel_number',)
    list_display_links = (
        'tabel_number',
        'person',
        'department',
        'tabel_number',
    )
    search_fields = ('tabel_number',)

    list_filter = ('department',)


class ResHolidays(admin.ModelAdmin):
    list_display = ('year', 'day',)
    list_display_links = ('year', 'day',)
    search_fields = (
        'year',
        'day',
    )

    list_filter = ('year',)


admin.site.register(models.Posts)
admin.site.register(models.Departments)
admin.site.register(models.Persons, ResPersons)
admin.site.register(models.TypeWorkTime)
admin.site.register(models.Employees, ResEmployees)
admin.site.register(models.Holidays, ResHolidays)
