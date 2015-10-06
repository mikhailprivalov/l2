# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_doctorprofile_labtype'),
        ('directions', '0019_napravleniya_who_create'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='napravleniya',
            name='who_create',
        ),
        migrations.AddField(
            model_name='napravleniya',
            name='doc_who_create',
            field=models.ForeignKey(related_name='who_create', to='users.DoctorProfile', null=True, default=None, blank=True),
        ),
    ]
