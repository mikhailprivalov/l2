# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_auto_20150609_0350'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='isLDAP_user',
            field=models.BooleanField(default=False),
        ),
    ]
