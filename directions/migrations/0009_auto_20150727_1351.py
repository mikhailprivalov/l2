# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0008_auto_20150727_1235'),
    ]

    operations = [
        migrations.CreateModel(
            name='TubesRelation',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='issledovaniya',
            name='tube',
        ),
        migrations.AddField(
            model_name='tubesrelation',
            name='issledovaniye',
            field=models.ForeignKey(to='directions.Issledovaniya'),
        ),
        migrations.AddField(
            model_name='tubesrelation',
            name='tube',
            field=models.ForeignKey(to='directions.TubesRegistration'),
        ),
    ]
