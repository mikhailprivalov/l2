# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0026_auto_20151216_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='issledovaniya',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=10),
        )
        #migrations.AddField(
        #    model_name='tubesregistration',
        #    name='daynum',
        #    field=models.IntegerField(blank=True, null=True, default=0),
        #),
        #migrations.AlterField(
        #    model_name='result',
        #    name='value',
        #    field=models.TextField(blank=True, null=True),
        #),
    ]
