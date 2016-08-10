from django.contrib.contenttypes.models import ContentType
from django.db import models

class SettingManager(models.Manager):
    def dict_for_object(self, object):
        ct = ContentType.get_for_model(object)
        pk = object.pk
        return dict(self.filter(object_id=pk, content_type__id=ct.id).values_list('name', 'value'))