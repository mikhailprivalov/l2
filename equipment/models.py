from django.db import models


class Equipment(models.Model):
    title = models.CharField(max_length=255, default="", blank=True, help_text="Наименование")
    sequence_study_instance_uid = models.CharField(max_length=255, default="", blank=True, null=True, help_text="Последовательность для поиска", db_index=True)
    hospital = models.ForeignKey('hospitals.Hospitals', default=None, null=True, blank=True, db_index=True, verbose_name='Медорганизация', on_delete=models.SET_NULL)
    manufacturer = models.CharField(max_length=255, default="", blank=True, null=True, help_text="tag 0008,0070", db_index=True)
    manufacturer_model_name = models.CharField(max_length=255, default="", blank=True, null=True, help_text="tag 0008,1090", db_index=True)
    station_name = models.CharField(max_length=255, default="", blank=True, null=True, help_text="tag 0008,1010", db_index=True)



    def __str__(self):
        return f"{self.hospital} {self.title}"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудования"
