# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-01 11:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0028_auto_20170123_1926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2017/2/1/'),
        ),
    ]