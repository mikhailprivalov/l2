from django.contrib import admin
from cash_registers.models import CashRegister, Shift


class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'ip_address', 'port', 'department', 'address']
    search_fields = (
        'pk',
        'title',
    )
    raw_id_fields = ['department']


class ShiftAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cash_register', 'open_at', 'close_at', 'operator']
    search_fields = ('pk', 'operator', 'cash_register')
    list_filter = ('operator',)
    raw_id_fields = ['operator', 'cash_register']


admin.site.register(CashRegister, CashRegisterAdmin)
admin.site.register(Shift, ShiftAdmin)
