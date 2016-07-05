# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('podrazdeleniya', '0003_subgroups_podrazdeleniye'),
    ]

    operations = [
        migrations.AddField(
            model_name='podrazdeleniya',
            name='gid_n',
            field=models.IntegerField(blank=True, null=True, default=None),
        ),
    ]
