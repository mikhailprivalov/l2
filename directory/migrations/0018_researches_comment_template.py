# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0017_auto_20160513_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='comment_template',
            field=models.IntegerField(null=True, blank=True, default=-1),
        ),
    ]
