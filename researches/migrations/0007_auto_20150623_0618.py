# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0006_auto_20150623_0606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tubes',
            name='id',
            field=models.AutoField(serialize=False, primary_key=True),
        ),
    ]
