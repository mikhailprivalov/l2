from django.contrib import admin
from django.utils.formats import date_format

from .models import (
    Employee,
    Position,
    Department,
    TypeWorkTimeEmployee,
    EmployeePosition,
    EmployeeWorkingHoursSchedule,
    WorkDayStatus,
    TimeTrackingDocument,
    TypeCheckTimeTrackingDocument,
    TimeTrackingStatus,
    CashRegister,
    PlanDepartment,
    EmployeePositionCountWorkDayPerMonth,
    EmployeeVacation,
    TabelDocument,
    FactTimeWork,
    TabelFactTimeWorkRaw,
    Holidays, DoctorProfileDepartment,
)


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


@admin.register(TypeWorkTimeEmployee)
class TypeWorkTimeEmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
    )
    list_filter = ('title',)
    search_fields = ('pk', 'title')
    ordering = ('pk', 'title')


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


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = (
        'employee_position',
        'accounting_day',
        'department',
        'received_terminal',
        'received_cash',
        'return_terminal',
        'return_cash',
    )


@admin.register(PlanDepartment)
class PlanDepartmentAdmin(admin.ModelAdmin):
    list_display = (
        'department',
        'month',
        'plan',
    )


@admin.register(EmployeePositionCountWorkDayPerMonth)
class EmployeePositionCountWorkDayPerMonthAdmin(admin.ModelAdmin):
    list_display = ('employee_position', 'count_work_day_per_month', 'month', 'plan_day_profit')


@admin.register(EmployeeVacation)
class EmployeeVacationAdmin(admin.ModelAdmin):
    list_display = ('employee_position_id', 'start', 'end', 'work_day_status_title')
    raw_id_fields = ('employee_position', 'work_day_status')

    @admin.display(description='Тип отпуска')
    def work_day_status_title(self, obj):
        return obj.work_day_status.title if obj.work_day_status else '—'


@admin.register(TabelDocument)
class TabelDocumentAdmin(admin.ModelAdmin):
    list_display = ("department_title", "month_tabel_title", "is_actual", "version", "status")
    list_select_related = ("department",)
    list_display_links = ("department_title", "month_tabel_title", "is_actual", "version", "status")

    list_filter = ("department", "is_actual", "status", "month_tabel")

    @admin.display(description="Месяц")
    def month_tabel_title(self, obj):
        return date_format(obj.month_tabel, "F, Y") if obj.month_tabel else "-"

    @admin.display(description="Подразделение")
    def department_title(self, obj):
        return obj.department.name if obj.department else "-"


@admin.register(FactTimeWork)
class TabelFactTimeWorkAdmin(admin.ModelAdmin):
    list_display = ("tabel_document", "employee_position", "date", "common_hours", "night_hours", "work_day_status")
    list_display_links = ("tabel_document", "employee_position", "date", "common_hours", "night_hours", "work_day_status")
    raw_id_fields = ("employee_position",)


@admin.register(TabelFactTimeWorkRaw)
class TabelDataAdmin(admin.ModelAdmin):
    list_display = ("tabel_document", "tabel_document_month")
    list_display_links = ("tabel_document", "tabel_document_month")
    list_select_related = ("tabel_document",)

    @admin.display(description="Месяц табеля")
    def tabel_document_month(self, obj):
        return date_format(obj.tabel_document.month_tabel, "F, Y") if obj.tabel_document else "-"


@admin.register(Holidays)
class HolidaysAdmin(admin.ModelAdmin):
    list_display = ("day", "kind", "shorten_minutes")
    list_filter = ("kind",)


@admin.register(DoctorProfileDepartment)
class DoctorProfileDepartmentAdmin(admin.ModelAdmin):
    list_display = ("doctor_profile", "department")
