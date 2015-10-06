# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0020_auto_20151006_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='napravleniya',
            name='doc_who_create',
            field=models.ForeignKey(to='users.DoctorProfile', null=True, related_name='doc_who_create', blank=True, default=None),
        ),
    ]
