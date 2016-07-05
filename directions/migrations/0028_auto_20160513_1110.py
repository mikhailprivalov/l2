# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0027_auto_20160513_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='tubesregistration',
            name='daynum',
            field=models.IntegerField(null=True, blank=True, default=0),
        ),
        migrations.AlterField(
            model_name='result',
            name='value',
            field=models.TextField(null=True, blank=True),
        ),
    ]
