# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0008_researches_no_attach'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researches',
            name='no_attach',
            field=models.IntegerField(null=True, blank=True, default=0),
        ),
    ]
