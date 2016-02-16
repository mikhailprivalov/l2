from django.db import models
import directory.models as directory_models
import uuid


class Application(models.Model):
    """
    Модель rest приложений для безопасного доступа по ключам
    """
    key = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RelationFractionASTM(models.Model):
    """
    Модель соответствия фракций из ASTM для LIS
    """
    MULTIPLIERS = ((0, 1), (1, 10), (2, 100), (3, 1000),)
    astm_field = models.CharField(max_length=127)
    fraction = models.ForeignKey(directory_models.Fractions)
    multiplier = models.IntegerField(choices=MULTIPLIERS, default=0)

    def __str__(self):
        return self.astm_field + " to \"" + self.fraction.research.title + "." + self.fraction.title + "\" x " + str(self.get_multiplier_display())
