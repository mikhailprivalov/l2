import clients.models as models
from django.contrib import admin

admin.site.register(models.Importedclients)


@admin.register(models.Individual)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(models.DocumentType)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Document)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CardBase)
class AuthorAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Card)
class AuthorAdmin(admin.ModelAdmin):
    pass
