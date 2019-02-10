from django.db import models

class FormsList(models.Model):
    title = models.CharField(max_length=255, default="", unique=True, help_text='Название формы',verbose_name='Имя формы')
    type_number = models.PositiveIntegerField(unique=True, blank=False, help_text='Номер типа формы',
                                              verbose_name='Внутренний номер формы')
    comment = models.CharField(max_length=255, default="", help_text='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки форм'
        verbose_name_plural = 'Списки форм'

class FormsTemplate(models.Model):
    form_name = models.ForeignKey(FormsList, help_text='Наименование формы',on_delete='Cascade',verbose_name='Имя формы')
    section_name = models.CharField(max_length=255,default="", blank=True, help_text='Название раздела/реквизита для формы',
                                    verbose_name='Реквизит/раздел на форме')
    is_print_section = models.BooleanField(default=False, verbose_name='Выводить на печать реквизит')
    template_text = models.TextField(help_text='Текст для формы', blank=True, default='',
                                     verbose_name='Текст реквизита для формы')

    def __str__(self):
        return "{}".format(self.form_name)


    class Meta:
        verbose_name = 'Cписки текстов для форм'
        verbose_name_plural = 'Списки текстов для форм'
