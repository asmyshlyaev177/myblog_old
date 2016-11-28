# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-23 16:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_auto_20161122_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='main_tag',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='blog.Tag'),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/11/23/'),
        ),
    ]
