# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podrazdeleniya', '0005_podrazdeleniya_islab'),
    ]

    operations = [
        migrations.AddField(
            model_name='podrazdeleniya',
            name='hide',
            field=models.BooleanField(default=False),
        ),
    ]
