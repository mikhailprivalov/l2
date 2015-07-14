# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0005_auto_20150625_1638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='napravleniya',
            name='istochnik_finansirovaniya',
        ),
    ]
