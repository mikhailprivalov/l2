from django.db import models


class Equipment(models.Model):
    title = models.CharField(max_length=255, default="", blank=True, help_text="Наименование")
    sequence_study_instance_uid = models.CharField(max_length=255, default="", blank=True, null=True, help_text="Последовательность для поиска", db_index=True)
    hospital = models.ForeignKey('hospitals.Hospitals', default=None, null=True, blank=True, db_index=True, verbose_name='Медорганизация', on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.hospital} {self.title}"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудования"
