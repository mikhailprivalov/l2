# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0005_fractions_max_iterations'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='edit_mode',
            field=models.IntegerField(default=0),
        ),
    ]
