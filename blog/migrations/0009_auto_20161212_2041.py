# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_auto_20161212_2034'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='user_last_login',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2016, 12, 12, 17, 41, 11, 719614, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='myuser',
            name='last_login',
            field=models.DateTimeField(verbose_name='last login', null=True, blank=True),
        ),
    ]
