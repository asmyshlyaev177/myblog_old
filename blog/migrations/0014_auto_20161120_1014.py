# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-20 10:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_auto_20161120_0951'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='voteuser',
            name='user',
        ),
        migrations.AddField(
            model_name='myuser',
            name='rateable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='post',
            name='rateable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='rateable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='uservotes',
            name='block_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='uservotes',
            name='manual',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='uservotes',
            name='weight',
            field=models.FloatField(default=0.25),
        ),
        migrations.AlterField(
            model_name='uservotes',
            name='votes',
            field=models.IntegerField(default=100),
        ),
        migrations.DeleteModel(
            name='VoteUser',
        ),
    ]
