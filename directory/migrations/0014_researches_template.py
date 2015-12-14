# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0013_absorption'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='template',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
