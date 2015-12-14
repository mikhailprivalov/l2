# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0014_researches_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='deferred',
            field=models.BooleanField(default=False),
        ),
    ]
