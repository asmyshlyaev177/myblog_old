# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-15 18:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_comment_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ratingpost',
            name='day',
        ),
        migrations.RemoveField(
            model_name='ratingpost',
            name='month',
        ),
        migrations.RemoveField(
            model_name='ratingpost',
            name='week',
        ),
        migrations.RemoveField(
            model_name='ratingtag',
            name='day',
        ),
        migrations.RemoveField(
            model_name='ratingtag',
            name='month',
        ),
        migrations.RemoveField(
            model_name='ratingtag',
            name='week',
        ),
        migrations.RemoveField(
            model_name='uservotes',
            name='votes',
        ),
        migrations.AlterField(
            model_name='post',
            name='post_image',
            field=models.ImageField(blank=True, upload_to='2016/12/15/'),
        ),
    ]