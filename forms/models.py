from django.db import models

class FormsList(models.Model):
    title = models.DecimalField(max_digits=5, decimal_places=2,unique=True,
                  help_text='Номер формы (3 знака целого числа-это группа, остальные- номер формы В ГРУППЕ)',db_index=True)
    is_active = models.BooleanField(default=True, help_text="Активность формы",db_index=True)
    comment = models.CharField(max_length=255, default="", blank=True, help_text='Описание')

    def __int__(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки форм'
        verbose_name_plural = 'Списки форм'

