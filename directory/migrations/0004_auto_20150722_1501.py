# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0003_auto_20150722_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fractions',
            name='uet_doc',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='uet_lab',
            field=models.FloatField(default=0),
        ),
    ]
