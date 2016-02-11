# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20160209_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationfractionastm',
            name='astm_field',
            field=models.CharField(max_length=127),
        ),
    ]
