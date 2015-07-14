# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0003_auto_20150615_0802'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='research',
            options={'managed': False},
        ),
    ]
