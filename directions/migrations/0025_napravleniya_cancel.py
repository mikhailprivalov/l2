# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0024_issledovaniya_deferred'),
    ]

    operations = [
        migrations.AddField(
            model_name='napravleniya',
            name='cancel',
            field=models.BooleanField(default=False),
        ),
    ]
