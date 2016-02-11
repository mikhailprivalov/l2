# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0025_napravleniya_cancel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issledovaniya',
            name='time_confirmation',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='issledovaniya',
            name='time_save',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
    ]
