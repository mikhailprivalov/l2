# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0004_auto_20150722_1501'),
        ('directions', '0007_tubesregistration_notice'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issledovaniya',
            name='issledovaniye',
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='research',
            field=models.ForeignKey(to='directory.Researches', blank=True, null=True),
        ),
    ]
