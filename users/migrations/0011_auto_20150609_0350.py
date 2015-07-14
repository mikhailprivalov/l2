# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0010_doctorprofile_podrazileniye'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorprofile',
            name='podrazileniye',
            field=models.ForeignKey(to='podrazdeleniya.Podrazdeleniya', blank=True, null=True),
        ),
    ]
