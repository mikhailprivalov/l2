# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0028_auto_20160513_1110'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issledovaniya',
            name='comment',
        ),
    ]
