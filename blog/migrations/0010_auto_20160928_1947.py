# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-28 16:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_auto_20160927_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/9/28/'),
        ),
    ]