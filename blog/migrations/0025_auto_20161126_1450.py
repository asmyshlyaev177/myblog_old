# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-26 14:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0024_auto_20161126_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='ratingpost',
            name='day',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ratingtag',
            name='day',
            field=models.FloatField(blank=True, null=True),
        ),
    ]