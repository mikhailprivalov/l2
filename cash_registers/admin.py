from django.contrib import admin

from cash_registers.models import CashRegister, Shift


# Register your models here.
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'ip_address', 'port']

    search_fields = (
        'pk',
        'title',
    )


class ShiftAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cash_register', 'open_at', 'close_at', 'operator']

    search_fields = (
        'pk',
        'operator',
        'cash_register'
    )


admin.site.register(CashRegister, CashRegisterAdmin)
admin.site.register(Shift, ShiftAdmin)
