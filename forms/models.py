from django.db import models

class FormsGroup(models.Model):
    title = models.CharField(max_length=255, default="", unique=True, help_text='Группа для форм')
    title_rus = models.CharField(max_length=25, default="", blank=True, help_text='GUI-название группы формы')
    comment = models.CharField(max_length=255, default="", blank=True, help_text='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа форм'
        verbose_name_plural = 'Группа форм'

class FormsList(models.Model):
    form_group = models.ForeignKey(FormsGroup, db_index=True, help_text='Наименование группы для форм', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="", unique=True, help_text='Название формы')
    title_rus = models.CharField(max_length=25, default="", blank=True, help_text='GUI-название формы')
    type_number = models.PositiveIntegerField(unique=True, blank=False, help_text='Номер типа формы')
    comment = models.CharField(max_length=255, default="", help_text='Описание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Cписки форм'
        verbose_name_plural = 'Списки форм'

class FormsTemplate(models.Model):
    form_name = models.ForeignKey(FormsList, help_text='Наименование формы',on_delete='Cascade')
    section_name = models.CharField(max_length=255,default="", blank=True, help_text='Название раздела/реквизита для формы')
    is_print_section = models.BooleanField(default=False)
    template_text = models.TextField(help_text='Текст для формы', blank=True, default='')

    def __str__(self):
        return "{}".format(self.form_name)


    class Meta:
        verbose_name = 'Cписки текстов для форм'
        verbose_name_plural = 'Списки текстов для форм'
