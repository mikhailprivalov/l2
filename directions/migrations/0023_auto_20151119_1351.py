# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0022_napravleniya_history_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='napravleniya',
            name='data_sozdaniya',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
