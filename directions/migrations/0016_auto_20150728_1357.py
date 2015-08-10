# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0015_result_iteration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='iteration',
            field=models.IntegerField(default=1, null=True),
        ),
    ]
