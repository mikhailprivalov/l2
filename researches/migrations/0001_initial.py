# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('podrazdeleniya', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Research',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('edenici_izmereniya', jsonfield.fields.JSONField()),
                ('ref_m', jsonfield.fields.JSONField()),
                ('ref_zh', jsonfield.fields.JSONField()),
                ('ref_title', jsonfield.fields.JSONField()),
                ('podrazdeleniye', models.ForeignKey(to='podrazdeleniya.Podrazdeleniya')),
            ],
        ),
    ]
