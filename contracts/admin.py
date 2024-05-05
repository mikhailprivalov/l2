from django.contrib import admin

from .models import PriceName, PriceCoast, Contract, Company, PriceCategory, CompanyDepartment, MedicalExamination, BillingRegister


class ResPriceCoast(admin.ModelAdmin):
    list_filter = ('price_name', 'price_name__active_status', 'research__podrazdeleniye', 'research__is_doc_refferal', 'research__is_treatment', 'research__is_stom')
    list_display = (
        'price_name',
        'research',
        'internal_code',
        'coast',
        'status',
    )
    list_display_links = (
        'price_name',
        'research',
        'internal_code',
        'coast',
    )
    search_fields = ('research__internal_code', 'research__title')
    ordering = ('research__internal_code',)

    def status(self, obj):
        return obj.price_name.status()

    status.short_description = 'Статус прайса'

    def internal_code(self, obj):
        return obj.research.internal_code


class ResCompany(admin.ModelAdmin):
    list_filter = (
        'active_status',
        'contract__price',
    )
    list_display = (
        'title',
        'contract',
        'price',
        'modifier',
        'active_status',
    )
    list_display_links = (
        'title',
        'contract',
    )

    def price(self, obj):
        return obj.get_price()

    def modifier(self, obj):
        return obj.get_modifier()

    price.short_description = "Прайс контракта"
    modifier.short_description = "Модификатор прайса"


class ResCompanyDepartment(admin.ModelAdmin):
    list_filter = ('company',)
    list_display = (
        'title',
        'company',
        'hide',
    )
    list_display_links = (
        'title',
        'company',
    )


class ResContract(admin.ModelAdmin):
    list_display = (
        'title',
        'price',
        'modifier',
        'active_status',
        'show_in_card',
    )
    list_display_links = ('title',)
    list_filter = (
        'price',
        'active_status',
        'show_in_card',
    )


class ResMedicalExamination(admin.ModelAdmin):
    list_display = ('card', 'company', 'date')
    list_display_links = ('card', 'company', 'date')
    list_filter = ('company', 'date')
    raw_id_fields = ('card',)
    autocomplete_fields = ('card',)


class ResBillingRegister(admin.ModelAdmin):
    list_display = ('company', 'hospital', 'date_start', 'date_end', 'price',)
    list_display_links = ('company', 'hospital',)
    list_filter = ('hospital', 'create_at',)


admin.site.register(PriceCategory)
admin.site.register(PriceName)
admin.site.register(Contract, ResContract)
admin.site.register(Company, ResCompany)
admin.site.register(CompanyDepartment, ResCompanyDepartment)
admin.site.register(PriceCoast, ResPriceCoast)
admin.site.register(MedicalExamination, ResMedicalExamination)
admin.site.register(BillingRegister, ResBillingRegister)
