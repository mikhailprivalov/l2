# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0011_auto_20150727_1437'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issledovaniya',
            name='resultat',
        ),
    ]
