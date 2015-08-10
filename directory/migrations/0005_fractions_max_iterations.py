# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0004_auto_20150722_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='fractions',
            name='max_iterations',
            field=models.IntegerField(default=1),
        ),
    ]
