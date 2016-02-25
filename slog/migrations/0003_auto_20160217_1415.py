# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slog', '0002_auto_20150805_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='body',
            field=models.CharField(max_length=2047),
        ),
        migrations.AlterField(
            model_name='log',
            name='key',
            field=models.CharField(max_length=2047),
        ),
    ]
