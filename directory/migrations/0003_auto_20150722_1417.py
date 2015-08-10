# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0002_auto_20150722_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researches',
            name='direction',
            field=models.ForeignKey(blank=True, null=True, to='directory.DirectionsGroup'),
        ),
    ]
