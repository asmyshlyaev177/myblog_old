# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-31 17:38
from __future__ import unicode_literals

import blog.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import imagekit.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='myUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('username', models.CharField(max_length=30, unique=True, verbose_name='Username')),
                ('avatar', imagekit.models.fields.ProcessedImageField(blank=True, upload_to=blog.models.myUser.user_directory_path)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('is_it_staff', models.BooleanField(default=False, verbose_name='Is stuff')),
                ('is_it_superuser', models.BooleanField(default=False, verbose_name='Is admin')),
                ('moderated', models.BooleanField(default=True, verbose_name='Moderated')),
                ('last_login', models.DateTimeField(auto_now=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'users',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True)),
                ('description', models.TextField(max_length=250)),
                ('slug', models.SlugField(blank=True, max_length=150, verbose_name='URL')),
                ('order', models.SmallIntegerField(blank=True, default=1)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.CharField(max_length=150)),
                ('text', models.TextField()),
                ('post_image', models.ImageField(blank=True, upload_to='2016/10/31/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('edited', models.DateTimeField(auto_now=True)),
                ('published', models.DateTimeField(default=django.utils.timezone.now)),
                ('private', models.BooleanField(default=False)),
                ('main_tag', models.CharField(blank=True, max_length=33)),
                ('url', models.SlugField(blank=True)),
                ('status', models.CharField(choices=[('D', 'Draft'), ('P', 'Published')], default='D', max_length=1)),
                ('author', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Category')),
            ],
            options={
                'verbose_name_plural': 'posts',
                'ordering': ['-published'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, unique=True)),
                ('url', models.CharField(max_length=40, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'tags',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='posts', related_query_name='tag', to='blog.Tag'),
        ),
    ]
