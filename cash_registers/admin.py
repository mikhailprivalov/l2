from django.contrib import admin
from cash_registers.models import CashRegister, Shift, Cheque, ChequeItems, ChequeForDirection


class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'ip_address', 'port', 'department', 'address']
    list_display_links = ['pk', 'title']
    search_fields = (
        'pk',
        'title',
    )
    raw_id_fields = ['department']


class ShiftAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cash_register', 'open_at', 'close_at', 'operator']
    list_display_links = ['pk', 'cash_register', 'operator']
    search_fields = ('pk', 'operator', 'cash_register')
    list_filter = ('operator',)
    raw_id_fields = ['operator', 'cash_register']


class ChequeAdmin(admin.ModelAdmin):
    list_display = ['pk', 'shift', 'type', 'status', 'payment_cash', 'payment_electronic']
    list_display_links = ['pk', 'shift', 'type']
    list_filter = ('status',)
    raw_id_fields = [
        'shift',
        'card',
    ]


class ChequeItemsAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cheque', 'research', 'coast', 'count', 'amount']
    list_display_links = ['pk', 'cheque', 'research']
    list_filter = ('cheque',)
    raw_id_fields = [
        'research',
    ]


class ChequeForDirectionAdmin(admin.ModelAdmin):
    list_display = ['pk', 'cheque', 'direction']
    list_display_links = ['pk', 'cheque', 'direction']
    raw_id_fields = [
        'cheque',
        'direction',
    ]


admin.site.register(CashRegister, CashRegisterAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Cheque, ChequeAdmin)
admin.site.register(ChequeItems, ChequeItemsAdmin)
admin.site.register(ChequeForDirection, ChequeForDirectionAdmin)
