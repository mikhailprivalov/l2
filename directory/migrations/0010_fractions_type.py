# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0009_auto_20150804_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='fractions',
            name='type',
            field=models.IntegerField(default=-1, blank=True, null=True),
        ),
    ]
