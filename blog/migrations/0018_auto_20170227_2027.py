# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-27 17:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_auto_20170227_2026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='rating',
            field=models.FloatField(default=0.0, verbose_name='Рейтинг'),
        ),
    ]