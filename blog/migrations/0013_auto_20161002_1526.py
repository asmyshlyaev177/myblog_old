# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-10-02 12:26
from __future__ import unicode_literals

from django.db import migrations
import imagekit.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_auto_20161002_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='avatar',
            field=imagekit.models.fields.ProcessedImageField(blank=True, upload_to='avatars'),
        ),
    ]