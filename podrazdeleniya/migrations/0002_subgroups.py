# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subgroups',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=255)),
            ],
        ),
    ]
