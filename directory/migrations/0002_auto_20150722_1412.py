# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researches',
            name='preparation',
            field=models.CharField(default='', max_length=2047),
        ),
        migrations.AlterField(
            model_name='researches',
            name='quota_oms',
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name='researches',
            name='title',
            field=models.CharField(default='', max_length=255),
        ),
    ]
