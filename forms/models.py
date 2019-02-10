from django.db import models

class FormsList(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название исследования')
    type_number = models.PositiveIntegerField(unique=True, blank=False, help_text='Номер типа формы')
    comment = models.CharField(max_length=255, default="", help_text='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки форм'
        verbose_name_plural = 'Списки форм'

class FormsTemplate(models.Model):
    form_name = models.ManyToManyField(FormsList, help_text='Наименование формы', on_delete=models.CASCADE)
    template_text = models.TextField(help_text='Текст для формы', blank=True, default='')
    section_name = models.CharField(max_length=255, blank=False, help_text='Название раздела для формы')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки текстов для форм'
        verbose_name_plural = 'Списки текстов для форм'
