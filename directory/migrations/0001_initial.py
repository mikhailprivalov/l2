# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0003_subgroups_podrazdeleniye'),
        ('researches', '0007_auto_20150623_0618'),
    ]

    operations = [
        migrations.CreateModel(
            name='DirectionsGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Fractions',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('units', models.CharField(max_length=255)),
                ('ref_m', jsonfield.fields.JSONField()),
                ('ref_f', jsonfield.fields.JSONField()),
                ('uet_doc', models.FloatField()),
                ('uet_lab', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='ReleationsFT',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('tube', models.ForeignKey(to='researches.Tubes')),
            ],
        ),
        migrations.CreateModel(
            name='Researches',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('quota_oms', models.IntegerField()),
                ('preparation', models.CharField(max_length=2047)),
                ('direction', models.ForeignKey(to='directory.DirectionsGroup')),
                ('subgroup', models.ForeignKey(to='podrazdeleniya.Subgroups', related_name='subgroup')),
            ],
        ),
        migrations.AddField(
            model_name='fractions',
            name='relation',
            field=models.ForeignKey(to='directory.ReleationsFT'),
        ),
        migrations.AddField(
            model_name='fractions',
            name='research',
            field=models.ForeignKey(to='directory.Researches'),
        ),
    ]
