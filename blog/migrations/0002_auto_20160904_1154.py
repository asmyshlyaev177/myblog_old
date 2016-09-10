# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-04 08:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='description',
            field=models.CharField(blank=True, max_length=400),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/9/4/'),
        ),
    ]