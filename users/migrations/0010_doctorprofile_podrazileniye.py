# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0001_initial'),
        ('users', '0009_auto_20150608_0659'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='podrazileniye',
            field=models.OneToOneField(null=True, to='podrazdeleniya.Podrazdeleniya', blank=True),
        ),
    ]
