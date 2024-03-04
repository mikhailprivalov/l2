from django.contrib import admin
from .models import Employee, Position, Department, EmployeePosition, EmployeeWorkingHoursSchedule, WorkDayStatus, TimeTrackingDocument, TypeCheckTimeTrackingDocument, TimeTrackingStatus


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


@admin.register(WorkDayStatus)
class WorkDayStatusAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_title')


@admin.register(TimeTrackingDocument)
class TimeTrackingDocumentAdmin(admin.ModelAdmin):
    list_display = ('create_at', 'month', 'department')


@admin.register(TypeCheckTimeTrackingDocument)
class TypeCheckTimeTrackingDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'hide')


@admin.register(TimeTrackingStatus)
class TimeTrackingStatusAdmin(admin.ModelAdmin):
    list_display = ('time_tracking_document', 'status', 'time_change_status')


@admin.register(EmployeeWorkingHoursSchedule)
class EmployeeWorkingHoursScheduleAdmin(admin.ModelAdmin):
    list_display = ('time_tracking_document', 'employee_position', 'day', 'work_day_status')
