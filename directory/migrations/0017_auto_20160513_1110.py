# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0016_remove_researches_deferred'),
    ]

    operations = [
        migrations.AddField(
            model_name='fractions',
            name='hide',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fractions',
            name='options',
            field=models.CharField(max_length=511, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='fractions',
            name='render_type',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
