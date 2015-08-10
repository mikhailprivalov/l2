# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0006_researches_edit_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='hide',
            field=models.BooleanField(default=False),
        ),
    ]
