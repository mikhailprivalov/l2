# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0005_researches_tubetypes'),
        ('users', '0011_auto_20150609_0350'),
        ('directions', '0002_auto_20150618_0046'),
    ]

    operations = [
        migrations.CreateModel(
            name='Issledovaniya',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('material_vremya_zabor', models.DateTimeField(null=True, blank=True)),
                ('material_vremya_prinyal', models.DateTimeField(null=True, blank=True)),
                ('resultat', jsonfield.fields.JSONField()),
                ('issledovaniye', models.ForeignKey(to='researches.Researches')),
                ('material_doc_prinyal', models.ForeignKey(null=True, blank=True, to='users.DoctorProfile',
                                                           related_name='material_doc_prinyal')),
                ('material_doc_zabor',
                 models.ForeignKey(null=True, blank=True, to='users.DoctorProfile', related_name='material_doc_zabor')),
            ],
        ),
        migrations.CreateModel(
            name='IstochnikiFinansirovaniya',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('tilie', models.CharField(max_length=511)),
                ('active_status', models.BooleanField(default=True)),
                ('istype', models.CharField(default='poli', max_length=4)),
            ],
        ),
        migrations.AlterField(
            model_name='napravleniya',
            name='istochnik_finansirovaniya',
            field=models.IntegerField(choices=[(0, 'ОМС'), (1, 'ДМС'), (2, 'платно')], default=0),
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='napravleniye',
            field=models.ForeignKey(to='directions.Napravleniya'),
        ),
        migrations.AddField(
            model_name='napravleniya',
            name='istochnik_f',
            field=models.ForeignKey(null=True, blank=True, to='directions.IstochnikiFinansirovaniya'),
        ),
    ]
