from django.db import models


class GroupDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = 'Группа Документов'
        verbose_name_plural = 'Группы документов'

    def __str__(self):
        return f'{self.title}'

    @property
    def json(self):
        return {
            'id': self.id,
            'title': self.title,
        }


class Attributes(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = 'Группа Документов'
        verbose_name_plural = 'Группы документов'

    def __str__(self):
        return f'{self.title}'


class TypeDocuments(models.Model):
    title = models.CharField(max_length=128, blank=True, null=True)
    group_document = models.ForeignKey(GroupDocuments, default=None, blank=True, null=True, help_text='Группа документов', on_delete=models.SET_NULL)
    code = models.CharField(max_length=55, blank=True, null=True)

    class Meta:
        verbose_name = 'Группа Документов'
        verbose_name_plural = 'Группы документов'

    def __str__(self):
        return f'{self.title}'

    @property
    def json(self):
        return {
            'id': self.id,
            'title': self.title,
        }


class TypeDocumentsAttributes(models.Model):
    type_document = models.ForeignKey(TypeDocuments, default=None, blank=True, null=True, help_text='Тип документа', on_delete=models.SET_NULL)
    attribute = models.ForeignKey(Attributes, default=None, blank=True, null=True, help_text='Тип реквизита', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Реквизит для документа'
        verbose_name_plural = 'Реквизит для документов'

    def __str__(self):
        return f'{self.type_document} {self.attribute}'
