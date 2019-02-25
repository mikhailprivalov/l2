from django.contrib import admin
from .models import PriceName, PriceCoast, Contract, Company
# Register your models here.
class ResPriceCoast(admin.ModelAdmin):
    list_filter = ('price_name','price_name__active_status',)
    list_display = ('price_name','research', 'coast','status',)
    list_display_links = ('price_name','research', 'coast',)

    def status(self, obj):
        return obj.price_name.status()

    status.short_description = 'Статус прайса'

class ResCompany(admin.ModelAdmin):
    list_filter = ('active_status',)
    list_display = ('title', 'active_status',)
    list_display_links = ('title',)

class ResContract(admin.ModelAdmin):
    list_display = ('title','company', 'price','active_status','show_in_research','show_in_card',)
    list_display_links = ('title',)
    list_filter = ('price','active_status','show_in_research','show_in_card',)



admin.site.register(PriceName)
admin.site.register(Contract, ResContract)
admin.site.register(Company, ResCompany)
admin.site.register(PriceCoast, ResPriceCoast)