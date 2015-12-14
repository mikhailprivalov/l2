# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0015_researches_deferred'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='researches',
            name='deferred',
        ),
    ]
