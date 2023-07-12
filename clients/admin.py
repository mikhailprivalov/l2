import clients.models as models
from django.contrib import admin


@admin.register(models.Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = (
        'family',
        'name',
        'patronymic',
        'birthday',
    )
    search_fields = ('family', 'name', 'patronymic')


@admin.register(models.DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('individual',)
    search_fields = ('number', 'serial', 'individual')


@admin.register(models.CardBase)
class CardBaseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Card)
class CardAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'individual',
        'polis',
        'mother',
        'father',
        'curator',
        'agent',
        'payer',
    )

    search_fields = ('pk', 'number')


@admin.register(models.ScreeningRegPlan)
class ScreeningRegPlanAdmin(admin.ModelAdmin):
    autocomplete_fields = ('card',)

    search_fields = ('research__title',)


@admin.register(models.Phones)
class PhonesAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AgeCache)
class AgeCacheAdmin(admin.ModelAdmin):
    pass


@admin.register(models.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_ginekolog',
        'code_poliklinika',
    )


@admin.register(models.DispensaryReg)
class DispensaryRegAdmin(admin.ModelAdmin):
    autocomplete_fields = ('card',)


@admin.register(models.BenefitType)
class BenefitTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.BenefitReg)
class BenefitRegAdmin(admin.ModelAdmin):
    autocomplete_fields = ('card',)


@admin.register(models.DispensaryRegPlans)
class ResDispensaryRegPlans(admin.ModelAdmin):
    autocomplete_fields = ('card',)
    list_display = (
        'card',
        'research',
        'speciality',
        'date',
    )
    list_display_links = (
        'card',
        'research',
        'speciality',
        'date',
    )
    search_fields = (
        'research__title',
        'speciality__title',
    )


@admin.register(models.CardControlParam)
class ResCardControlParam(admin.ModelAdmin):
    list_display = (
        'card',
        'patient_control_param',
        'purpose_value',
        'date_start',
        'date_end',
    )

    list_display_links = (
        'card',
        'patient_control_param',
        'purpose_value',
        'date_start',
        'date_end',
    )
    raw_id_fields = ('card',)

    search_fields = ('card__pk',)


@admin.register(models.HarmfulFactor)
class ResHarmfulFactor(admin.ModelAdmin):
    autocomplete_fields = ['template']

    list_display = (
        'title',
        'description',
    )
    list_display_links = (
        'title',
        'description',
    )


@admin.register(models.PatientHarmfullFactor)
class ResPatientHarmfullFactor(admin.ModelAdmin):
    list_display = (
        'card',
        'harmful_factor',
    )
    list_display_links = (
        'card',
        'harmful_factor',
    )
    raw_id_fields = (
        'card',
        'harmful_factor',
    )


@admin.register(models.CardMovementRoom)
class ResCardMovementRoom(admin.ModelAdmin):
    list_display = (
        'card',
        'room_out',
        'room_in',
        'doc_who_issued',
        'date_issued',
        'doc_who_received',
        'date_received',
    )
    list_display_links = (
        'card',
        'room_out',
        'room_in',
    )
    raw_id_fields = ('card',)
