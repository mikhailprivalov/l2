import re
from django.db import models
from django.contrib.auth.models import Group

from laboratory.utils import strfdatetime


class Directory(models.Model):
    title = models.CharField(max_length=128, db_index=True, verbose_name='Название')
    code = models.CharField(max_length=64, db_index=True, verbose_name='Код справочника', blank=True, default='')
    root_directory = models.ForeignKey(
        'dynamic_directory.Directory',
        db_index=True,
        blank=True,
        null=True,
        default=None,
        verbose_name='Родительский справочник',
        on_delete=models.CASCADE,
        related_name='directory_root_directory',
    )
    hide = models.BooleanField(db_index=True, blank=True, default=False, verbose_name='Скрыт')
    without_history = models.BooleanField(db_index=True, blank=True, default=False, verbose_name='Без истории изменений')
    str_value_template = models.TextField(
        default='', blank=True, verbose_name='Шаблон текстового значения для записи (не забыть {title})'
    )  # пример "{title} {23} {24}" — поля с id=23,24 и название записи в title будут подставлены в соответствующие места
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    edit_access = models.ManyToManyField(Group, help_text="Группы пользователей, которые могут редактировать справочник", blank=True, default=None)

    def to_json(self):
        return {
            'pk': self.pk,
            'title': self.title,
            'code': self.code,
            'hide': self.hide,
            'rows': DirectoryRecord.objects.filter(directory=self).count(),
            'createdAt': strfdatetime(self.created_at, "%d.%m.%Y %X"),
            'updatedAt': strfdatetime(self.updated_at, "%d.%m.%Y %X"),
            'editAccess': [str(x) for x in self.edit_access.all()],
            'strValueTemplate': self.str_value_template or '{title}',
        }

    def to_treeselect_json(self):
        return {
            'id': self.pk,
            'label': self.title,
        }

    def recuresive_updated_at_change(self):
        self.save()
        if self.root_directory:
            self.root_directory.save()

    def get_fields(self):
        fields = {}
        q_fields = DirectoryField.objects.filter(directory=self, hide=False).order_by('order')

        for field in q_fields:
            fields[field.pk] = {
                'title': field.title,
                'type': field.field_type,
            }

        return fields

    def get_fields_extended(self):
        fields = {}
        q_fields = DirectoryField.objects.filter(directory=self, hide=False).order_by('order')

        for field in q_fields:
            default_value = None if field.field_type == 4 else field.default_value
            fields[field.pk] = {
                'title': field.title,
                'type': field.field_type,
                'isRequired': field.required,
                'defaultValue': default_value,
                'linkedDirectory': field.linked_directory_id,
                'value': default_value,
            }

        return fields

    def __str__(self) -> str:
        return f'{self.title} {self.code}'

    class Meta:
        verbose_name = 'Справочник'
        verbose_name_plural = 'Справочники'


class DirectoryField(models.Model):
    TYPES = (
        (0, 'Одна строка текста'),
        (1, 'Многострочный текст'),
        (2, 'Число'),
        (3, 'Дата'),
        (4, 'Справочник'),
    )

    directory = models.ForeignKey('dynamic_directory.Directory', db_index=True, verbose_name='Справочник', on_delete=models.CASCADE, related_name='field_directory')
    title = models.CharField(max_length=128, db_index=True, verbose_name='Название')
    field_type = models.SmallIntegerField(choices=TYPES, verbose_name='Тип')
    order = models.IntegerField(verbose_name='Порядковый вес')
    hide = models.BooleanField(db_index=True, blank=True, default=False, verbose_name='Скрыт')
    required = models.BooleanField(default=False, blank=True, verbose_name='Запрет пустого')
    default_value = models.TextField(verbose_name='Значение по умолчанию', blank=True, default='')
    linked_directory = models.ForeignKey(
        'dynamic_directory.Directory',
        db_index=True,
        verbose_name='Справочник для значения',
        blank=True,
        null=True,
        default=None,
        on_delete=models.CASCADE,
        related_name='field_value_directory',
    )

    def __str__(self) -> str:
        return f'{self.directory} — {self.title}, {self.get_field_type_display()}'

    class Meta:
        verbose_name = 'Поле справочника'
        verbose_name_plural = 'Поля справочников'


class DirectoryRecord(models.Model):
    directory = models.ForeignKey('dynamic_directory.Directory', db_index=True, verbose_name='Справочник', on_delete=models.CASCADE)
    title = models.CharField(max_length=128, db_index=True, verbose_name='Название')
    code = models.CharField(max_length=64, db_index=True, verbose_name='Код', blank=True, default='')
    last_version = models.IntegerField(default=0, blank=True, verbose_name='Последняя версия')
    hide = models.BooleanField(db_index=True, blank=True, default=False, verbose_name='Скрыт')
    last_str_value = models.TextField(db_index=True, verbose_name='Кэш последней версии строкового представления', blank=True, default='')

    def get_last_version(self):
        return self.get_version(self.last_version)

    def get_version(self, version):
        v = DirectoryRecordVersion.objects.filter(record=self, version=version)[0]
        result = {
            'pk': self.pk,
            'versionPk': v.pk,
            'directory': self.directory_id,
            'title': self.title,
            'code': self.code,
            'string': v.make_str_value(),
            'fields': {x.field_id: x.make_str_value() for x in DirectoryRecordValue.objects.filter(record_version=v)},
        }

        if not self.last_str_value:
            self.last_str_value = result['string']
            self.save()

        return result

    def __str__(self) -> str:
        return f'{self.directory} — {self.title} {self.code}'

    class Meta:
        verbose_name = 'Запись справочника'
        verbose_name_plural = 'Записи справочников'


class DirectoryRecordVersion(models.Model):
    record = models.ForeignKey('dynamic_directory.DirectoryRecord', db_index=True, verbose_name='Запись', on_delete=models.CASCADE)
    version = models.IntegerField(default=0, blank=True, db_index=True, verbose_name='Версия')

    def make_str_value(self):
        template: str = self.record.directory.str_value_template or self.record.title
        pks_regex = r"({\d+})"
        pks_groups = re.findall(pks_regex, template, flags=re.MULTILINE)
        vals = {x.replace('{', '').replace('}', ''): '' for x in pks_groups}
        for v in vals:
            record_value = DirectoryRecordValue.get_record_value_by_field_pk_and_version(self, v)
            if record_value:
                vals[v] = record_value.make_str_value()
            template = template.replace(f"{{{v}}}", vals[v])
        template = template.replace('{title}', self.record.title)
        return template

    def __str__(self) -> str:
        return f'{self.record}, v{self.version}'

    class Meta:
        verbose_name = 'Версия записи справочника'
        verbose_name_plural = 'Версии записей справочников'


class DirectoryRecordValue(models.Model):
    record_version = models.ForeignKey('dynamic_directory.DirectoryRecordVersion', db_index=True, verbose_name='Версия записи', on_delete=models.CASCADE)
    field = models.ForeignKey('dynamic_directory.DirectoryField', db_index=True, verbose_name='Поле справочника', on_delete=models.CASCADE)
    linked_directory_record = models.ForeignKey(
        'dynamic_directory.DirectoryRecordVersion',
        db_index=True,
        default=None,
        blank=True,
        null=True,
        verbose_name='Значение поля справочника',
        on_delete=models.CASCADE,
        related_name='linked_directory_record_val',
    )
    text_value = models.TextField(default='', blank=True, verbose_name='Текстовое значение')

    @staticmethod
    def get_record_value_by_field_pk_and_version(version, field_pk):
        return DirectoryRecordValue.objects.filter(record_version=version, field_id=field_pk).first()

    def make_str_value(self):
        if self.linked_directory_record:
            return self.linked_directory_record.make_str_value()
        return self.text_value

    def __str__(self) -> str:
        return f'{self.record_version}, {self.field}'

    class Meta:
        verbose_name = 'Значение справочника'
        verbose_name_plural = 'Значения справочников'
