# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0005_researches_tubetypes'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TubeTypes',
            new_name='Tubes',
        ),
    ]
