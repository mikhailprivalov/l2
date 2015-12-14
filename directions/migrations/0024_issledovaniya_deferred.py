# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0023_auto_20151119_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='issledovaniya',
            name='deferred',
            field=models.BooleanField(default=False),
        ),
    ]
