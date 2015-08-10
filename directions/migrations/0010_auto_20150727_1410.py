# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0009_auto_20150727_1351'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tubesrelation',
            name='issledovaniye',
        ),
        migrations.RemoveField(
            model_name='tubesrelation',
            name='tube',
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='tubes',
            field=models.ManyToManyField(to='directions.TubesRegistration'),
        ),
        migrations.DeleteModel(
            name='TubesRelation',
        ),
    ]
