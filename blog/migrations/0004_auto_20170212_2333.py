# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 20:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_auto_20170212_2329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='moder_cat',
            field=models.ManyToManyField(blank=True, null=True, to='blog.Category', verbose_name='Модерирует категории'),
        ),
    ]