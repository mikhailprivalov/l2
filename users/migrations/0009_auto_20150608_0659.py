# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0008_auto_20150608_0122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorprofile',
            name='user',
            field=models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
