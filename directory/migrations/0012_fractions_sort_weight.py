# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0011_researches_sort_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='fractions',
            name='sort_weight',
            field=models.IntegerField(default=0, blank=True, null=True),
        ),
    ]
