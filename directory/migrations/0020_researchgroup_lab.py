# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0007_merge'),
        ('directory', '0019_auto_20160622_0930'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchgroup',
            name='lab',
            field=models.ForeignKey(blank=True, null=True, to='podrazdeleniya.Podrazdeleniya'),
        ),
    ]
