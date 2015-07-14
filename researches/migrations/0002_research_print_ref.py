# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='research',
            name='print_ref',
            field=models.CharField(default=1, max_length=511),
            preserve_default=False,
        ),
    ]
