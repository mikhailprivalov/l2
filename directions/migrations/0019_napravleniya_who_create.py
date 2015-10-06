# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_doctorprofile_labtype'),
        ('directions', '0018_auto_20150803_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='napravleniya',
            name='who_create',
            field=models.ForeignKey(related_name='who_create', blank=True, default=None, to='users.DoctorProfile', null=True),
        ),
    ]
