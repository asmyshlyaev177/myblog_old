# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-09 16:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0021_auto_20170303_0739'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='main_image_srcset',
            field=models.TextField(blank=True, max_length=800, null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, max_length=400, null=True, upload_to='2017/3/9/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=150, verbose_name='Заголовок'),
        ),
    ]