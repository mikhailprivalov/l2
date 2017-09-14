import clients.models as models
from django.contrib import admin

admin.site.register(models.Importedclients)


@admin.register(models.Individual)
class IndividualAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CardBase)
class CardBaseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    exclude = ('individual',)
