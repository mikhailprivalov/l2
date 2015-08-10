# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0004_auto_20150722_1501'),
        ('directions', '0012_remove_issledovaniya_resultat'),
    ]

    operations = [
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('value', models.CharField(max_length=255)),
                ('fraction', models.ForeignKey(to='directory.Fractions')),
                ('issledovaniye', models.ForeignKey(to='directions.Issledovaniya')),
            ],
        ),
    ]
