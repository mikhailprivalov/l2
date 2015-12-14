# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0012_fractions_sort_weight'),
        ('api', '0002_application_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelationFractionASTM',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('astm_field', models.CharField(max_length=127)),
                ('multiplier', models.IntegerField(choices=[(0, 1), (1, 10), (2, 100), (3, 1000)], default=0)),
                ('fraction', models.ForeignKey(to='directory.Fractions')),
            ],
        ),
    ]
