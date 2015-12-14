# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0012_fractions_sort_weight'),
    ]

    operations = [
        migrations.CreateModel(
            name='Absorption',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('flower', models.ForeignKey(related_name='flower', to='directory.Fractions')),
                ('fupper', models.ForeignKey(related_name='fupper', to='directory.Fractions')),
            ],
        ),
    ]
