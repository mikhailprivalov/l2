from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.defaultfilters import truncatechars


class SettingR(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    value_type = models.CharField(max_length=1, choices=(('s', 'string'), ('i', 'integer'),
                                                         ('f', 'float'), ('b', 'boolean')))
    hide_value_in_list = models.BooleanField(default=False)

    def __str__(self):
        return "%s = %s (%s)" % (self.name, "**скрыто**" if self.hide_value_in_list else truncatechars(self.value, 150),
                                 self.get_value_type_display())

    def get_value(self):
        val = self.value
        types = {
            's': str,
            'i': int,
            'b': (lambda v: v.lower() == "true"),
            'f': float
        }
        return types[self.value_type](val)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры'
