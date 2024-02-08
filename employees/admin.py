from django.contrib import admin
from .models import Employee, Position, Department, EmployeePosition


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'family', 'name', 'patronymic', 'is_active')
    list_filter = ('hospital', 'is_active')
    search_fields = ('hospital', 'family', 'name', 'patronymic')
    ordering = ('hospital', 'family', 'name', 'patronymic', 'is_active')
    autocomplete_fields = ('hospital', 'doctorprofile_created', 'doctorprofile_updated')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'name', 'is_active')
    list_filter = ('hospital', 'is_active')
    search_fields = ('hospital', 'name')
    ordering = ('hospital', 'name', 'is_active')
    autocomplete_fields = ('hospital', 'doctorprofile_created', 'doctorprofile_updated')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'name', 'is_active')
    list_filter = ('hospital', 'is_active')
    search_fields = ('hospital', 'name')
    ordering = ('hospital', 'name', 'is_active')
    autocomplete_fields = ('hospital', 'doctorprofile_created', 'doctorprofile_updated')


@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'department', 'position', 'is_active')
    list_filter = ('employee', 'department', 'position', 'is_active')
    search_fields = ('employee', 'department', 'position')
    ordering = ('employee', 'department', 'position', 'is_active')
    autocomplete_fields = ('employee', 'department', 'doctorprofile_created', 'doctorprofile_updated')
