# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-27 07:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0025_auto_20161126_1450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/11/27/'),
        ),
    ]
