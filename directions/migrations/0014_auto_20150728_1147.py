# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0013_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='value',
            field=models.CharField(blank=True, null=True, max_length=255),
        ),
    ]
