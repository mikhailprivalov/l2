# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('researches', '0002_research_print_ref'),
    ]

    operations = [
        migrations.RenameField(
            model_name='research',
            old_name='podrazdeleniye',
            new_name='id_lab_fk',
        ),
        migrations.RenameField(
            model_name='research',
            old_name='edenici_izmereniya',
            new_name='ref_fractions',
        ),
        migrations.RemoveField(
            model_name='research',
            name='id',
        ),
        migrations.RemoveField(
            model_name='research',
            name='print_ref',
        ),
        migrations.RemoveField(
            model_name='research',
            name='title',
        ),
        migrations.AddField(
            model_name='research',
            name='id_research',
            field=models.IntegerField(default=1, primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='research',
            name='ref_units',
            field=jsonfield.fields.JSONField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='research',
            name='ref_title',
            field=models.CharField(max_length=511),
        ),
    ]
