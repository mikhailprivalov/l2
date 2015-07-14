# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Importedclients',
            fields=[
                ('num', models.IntegerField(unique=True, null=True, blank=True)),
                ('family', models.CharField(null=True, blank=True, max_length=255)),
                ('name', models.CharField(null=True, blank=True, max_length=255)),
                ('twoname', models.CharField(null=True, blank=True, max_length=255)),
                ('birthday', models.CharField(null=True, blank=True, max_length=255)),
                ('client_id', models.AutoField(primary_key=True, unique=True, serialize=False)),
                ('type', models.CharField(null=True, blank=True, max_length=64)),
                ('sex', models.CharField(null=True, blank=True, max_length=16)),
                ('initials', models.CharField(null=True, blank=True, max_length=16)),
            ],
            options={
                'db_table': 'ImportedClients',
                'managed': False,
            },
        ),
    ]
