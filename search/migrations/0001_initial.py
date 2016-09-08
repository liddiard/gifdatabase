# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-08 00:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(choices=[(b'mi', b'404 not found'), (b'in', b'inappropriate content'), (b'du', b'duplicate')], max_length=2)),
                ('date_flagged', models.DateTimeField(auto_now_add=True)),
                ('addressed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Gif',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=32, unique=True)),
                ('host', models.CharField(choices=[(b'ig', b'imgur')], default=b'ig', max_length=2)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('stars', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-date_added'],
            },
        ),
        migrations.CreateModel(
            name='SubstitutionProposal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proposed_gif', models.CharField(max_length=32)),
                ('host', models.CharField(choices=[(b'ig', b'imgur')], default=b'ig', max_length=2)),
                ('date_proposed', models.DateTimeField(auto_now_add=True)),
                ('accepted', models.BooleanField(default=False)),
                ('current_gif', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.Gif')),
            ],
        ),
        migrations.CreateModel(
            name='TagInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ups', models.PositiveIntegerField(default=0)),
                ('downs', models.PositiveIntegerField(default=0)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('content_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_taginstance_items', to='search.Gif', verbose_name=b'on')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_taginstance_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TagVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('up', models.BooleanField()),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.TagInstance')),
            ],
        ),
        migrations.CreateModel(
            name='UserFavorite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_favorited', models.DateTimeField(auto_now_add=True)),
                ('gif', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.Gif')),
            ],
            options={
                'ordering': ['-date_favorited'],
            },
        ),
        migrations.CreateModel(
            name='UserScore',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('score', models.IntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='userfavorite',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tagvote',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taginstance',
            name='user_added',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='substitutionproposal',
            name='user_proposed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gif',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='search.TagInstance', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='gif',
            name='user_added',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='flag',
            name='duplicate',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='duplicate', to='search.Gif'),
        ),
        migrations.AddField(
            model_name='flag',
            name='gif',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='current', to='search.Gif'),
        ),
        migrations.AddField(
            model_name='flag',
            name='user_flagged',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
