# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_relationfractionastm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationfractionastm',
            name='astm_field',
            field=models.CharField(unique=True, max_length=127),
        ),
    ]
