# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-13 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_auto_20160913_2026'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='username',
            field=models.CharField(max_length=30, unique=True, verbose_name='Username'),
        ),
    ]