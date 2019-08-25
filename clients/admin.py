import clients.models as models
from django.contrib import admin


class ResIndividual(admin.ModelAdmin):
    search_fields = ('family', )
    ordering = ('family',)


admin.site.register(models.Individual, ResIndividual)

@admin.register(models.DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    raw_id_fields = ('individual',)


@admin.register(models.CardBase)
class CardBaseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('individual', 'polis',)


@admin.register(models.Phones)
class PhonesAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AgeCache)
class AgeCacheAdmin(admin.ModelAdmin):
    pass


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DispensaryReg)
class DispensaryRegAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)


@admin.register(models.BenefitType)
class DispensaryRegAdmin(admin.ModelAdmin):
    pass


@admin.register(models.BenefitReg)
class DispensaryRegAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)
