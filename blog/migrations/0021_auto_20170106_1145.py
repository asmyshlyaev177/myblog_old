# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-06 08:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_auto_20161225_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2017/1/6/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_thumbnail',
            field=models.ImageField(blank=True, upload_to='2017/1/6/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Заголовок'),
        ),
    ]