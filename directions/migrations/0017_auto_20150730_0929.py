# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_auto_20150609_0350'),
        ('directions', '0016_auto_20150728_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='issledovaniya',
            name='doc_confirmation',
            field=models.ForeignKey(null=True, to='users.DoctorProfile', blank=True, related_name='doc_confirmation'),
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='doc_save',
            field=models.ForeignKey(null=True, to='users.DoctorProfile', blank=True, related_name='doc_save'),
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='time_confirmation',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='time_save',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='napravleniya',
            name='is_printed',
            field=models.BooleanField(default=False),
        ),
    ]
