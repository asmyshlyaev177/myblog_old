# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-03 04:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_auto_20170227_2042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, null=True, upload_to='2017/3/3/'),
        ),
    ]