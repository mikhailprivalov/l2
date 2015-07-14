# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0004_auto_20150615_0835'),
    ]

    operations = [
        migrations.CreateModel(
            name='Researches',
            fields=[
                ('id_research', models.AutoField(serialize=False, primary_key=True)),
                ('ref_title', models.CharField(null=True, blank=True, max_length=255)),
                ('ref_fractions', jsonfield.fields.JSONField(null=True, blank=True)),
                ('ref_m', jsonfield.fields.JSONField(null=True, blank=True)),
                ('ref_f', jsonfield.fields.JSONField(null=True, blank=True)),
                ('ref_units', jsonfield.fields.JSONField(null=True, blank=True)),
                ('group', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'managed': False,
                'db_table': 'researches',
            },
        ),
        migrations.CreateModel(
            name='TubeTypes',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('color', models.CharField(max_length=7)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
    ]
