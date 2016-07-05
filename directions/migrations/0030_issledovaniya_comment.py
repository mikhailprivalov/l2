# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0029_remove_issledovaniya_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='issledovaniya',
            name='comment',
            field=models.CharField(default='', blank=True, max_length=10),
        ),
    ]
