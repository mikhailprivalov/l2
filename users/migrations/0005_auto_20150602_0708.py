# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_auto_20150602_0704'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clienty',
            name='id',
        ),
        migrations.AddField(
            model_name='clienty',
            name='cardnum',
            field=models.IntegerField(primary_key=True, serialize=False, default=1, db_index=True),
            preserve_default=False,
        ),
    ]
