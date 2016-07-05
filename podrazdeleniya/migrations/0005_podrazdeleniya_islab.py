# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podrazdeleniya', '0004_podrazdeleniya_gid_n'),
    ]

    operations = [
        migrations.AddField(
            model_name='podrazdeleniya',
            name='isLab',
            field=models.BooleanField(default=False),
        ),
    ]
