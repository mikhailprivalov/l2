# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_auto_20150609_0350'),
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Napravleniya',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('data_sozdaniya', models.DateTimeField(auto_now=True)),
                ('diagnos', models.CharField(max_length=511)),
                ('istochnik_finansirovaniya',
                 models.IntegerField(choices=[(0, 'ДМС'), (1, 'ОМС'), (2, 'платно')], max_length=1)),
                ('client', models.ForeignKey(to='clients.Importedclients')),
                ('doc', models.ForeignKey(to='users.DoctorProfile')),
            ],
        ),
    ]
