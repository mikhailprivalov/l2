from django.contrib import admin
from .models import Medicament


class ResMedicament(admin.ModelAdmin):
    list_display = ('trade_name','international_name','pharm_group','number_registration',)
    list_display_links = ('trade_name','international_name',)
    list_filter = ('pharm_group',)
    search_fields = ('trade_name','international_name','pharm_group',)


admin.site.register(Medicament, ResMedicament)
