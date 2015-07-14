# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_auto_20150602_0700'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clienty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('fio', models.CharField(max_length=255)),
            ],
        ),
        migrations.DeleteModel(
            name='Clienti',
        ),
    ]
