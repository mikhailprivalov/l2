# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0007_researches_hide'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='no_attach',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
