from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template.defaultfilters import truncatechars

class Setting(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    value_type = models.CharField(max_length=1, choices=(('s', 'string'), ('i', 'integer'),
                                                         ('f', 'float'), ('b', 'boolean')))

    def __str__(self):
        return "%s = %s (%s)" % (self.name, truncatechars(self.value, 150), self.get_value_type_display())

    def nval(self):
        val = self.value
        types = {
            's': str,
            'i': int,
            'b': (lambda v: v.lower().startswith('t') or v.startswith('1')),
            'f': float
        }
        return types[self.value_type](val)

    def save(self, *args, **kwargs):
        super(Setting, self).save(*args, **kwargs)
        #from django.core.cache import cache
        #cache.delete(self.name)
        #cache.set(self.name, self.nval(), 60 * 60 * 8)
