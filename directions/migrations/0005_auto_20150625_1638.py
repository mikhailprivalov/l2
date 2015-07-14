# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0004_auto_20150625_1019'),
    ]

    operations = [
        migrations.AddField(
            model_name='tubesregistration',
            name='barcode',
            field=models.CharField(null=True, blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='tubesregistration',
            name='id',
            field=models.AutoField(serialize=False, primary_key=True),
        ),
    ]
