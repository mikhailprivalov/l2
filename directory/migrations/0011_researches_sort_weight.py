# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0010_fractions_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='sort_weight',
            field=models.IntegerField(null=True, blank=True, default=0),
        ),
    ]
