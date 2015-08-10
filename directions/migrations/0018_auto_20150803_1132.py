# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_auto_20150609_0350'),
        ('directions', '0017_auto_20150730_0929'),
    ]

    operations = [
        migrations.AddField(
            model_name='napravleniya',
            name='doc_print',
            field=models.ForeignKey(default=None, null=True, to='users.DoctorProfile', related_name='doc_print',
                                    blank=True),
        ),
        migrations.AddField(
            model_name='napravleniya',
            name='time_print',
            field=models.DateTimeField(default=None, blank=True, null=True),
        ),
    ]
