# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('directions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='napravleniya',
            name='istochnik_finansirovaniya',
            field=models.IntegerField(choices=[(0, 'ДМС'), (1, 'ОМС'), (2, 'платно')]),
        ),
    ]
