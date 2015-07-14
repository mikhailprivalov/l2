# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0007_auto_20150623_0618'),
        ('users', '0011_auto_20150609_0350'),
        ('directions', '0003_auto_20150623_0550'),
    ]

    operations = [
        migrations.CreateModel(
            name='TubesRegistration',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('time_get', models.DateTimeField(null=True, blank=True)),
                ('time_recive', models.DateTimeField(null=True, blank=True)),
                ('doc_get', models.ForeignKey(null=True, to='users.DoctorProfile', blank=True, related_name='docget')),
                ('doc_recive',
                 models.ForeignKey(null=True, to='users.DoctorProfile', blank=True, related_name='docrecive')),
                ('type', models.ForeignKey(to='researches.Tubes')),
            ],
        ),
        migrations.RemoveField(
            model_name='issledovaniya',
            name='material_doc_prinyal',
        ),
        migrations.RemoveField(
            model_name='issledovaniya',
            name='material_doc_zabor',
        ),
        migrations.RemoveField(
            model_name='issledovaniya',
            name='material_vremya_prinyal',
        ),
        migrations.RemoveField(
            model_name='issledovaniya',
            name='material_vremya_zabor',
        ),
        migrations.AddField(
            model_name='issledovaniya',
            name='tube',
            field=models.ForeignKey(null=True, to='directions.TubesRegistration', blank=True),
        ),
    ]
