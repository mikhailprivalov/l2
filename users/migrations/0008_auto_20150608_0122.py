# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0007_xlsprofilesync'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='xlsprofilesync',
            options={'verbose_name_plural': 'stories', 'managed': False, 'verbose_name': 'pizza'},
        ),
    ]
