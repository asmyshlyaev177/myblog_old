# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-08 16:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0023_auto_20170108_1901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image_url',
            field=models.URLField(blank=True, max_length=1300, null=True),
        ),
    ]