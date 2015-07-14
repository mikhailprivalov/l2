# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_clients_fio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clienti',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fio', models.CharField(null=True, max_length=255)),
            ],
        ),
        migrations.DeleteModel(
            name='Clients',
        ),
    ]
