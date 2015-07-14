# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0006_auto_20150608_0050'),
    ]

    operations = [
        migrations.CreateModel(
            name='XlsProfileSync',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('xls', models.FileField(upload_to='')),
            ],
            options={
                'managed': False,
            },
        ),
    ]
