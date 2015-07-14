# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0006_remove_napravleniya_istochnik_finansirovaniya'),
    ]

    operations = [
        migrations.AddField(
            model_name='tubesregistration',
            name='notice',
            field=models.CharField(default='', max_length=512),
        ),
    ]
