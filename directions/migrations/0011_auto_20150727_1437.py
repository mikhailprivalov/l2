# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0010_auto_20150727_1410'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tubesregistration',
            name='type',
            field=models.ForeignKey(to='directory.ReleationsFT'),
        ),
    ]
