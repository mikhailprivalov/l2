# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0002_subgroups'),
    ]

    operations = [
        migrations.AddField(
            model_name='subgroups',
            name='podrazdeleniye',
            field=models.ForeignKey(to='podrazdeleniya.Podrazdeleniya', default=1),
            preserve_default=False,
        ),
    ]
