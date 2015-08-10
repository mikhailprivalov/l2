# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0014_auto_20150728_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='iteration',
            field=models.IntegerField(default=1),
        ),
    ]
