# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-09 18:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_auto_20161007_0700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/10/9/'),
        ),
    ]