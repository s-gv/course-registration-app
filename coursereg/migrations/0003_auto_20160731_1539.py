# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-31 15:39
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('coursereg', '0002_user_telephone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('points', models.DecimalField(decimal_places=3, default=Decimal('0.00'), max_digits=10)),
                ('should_count_towards_cgpa', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('year', models.CharField(max_length=4)),
                ('start_reg_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_reg_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_adviser_approval_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_instructor_approval_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_cancellation_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_conversion_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_drop_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_grade_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('should_count_towards_cgpa', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Config',
        ),
        migrations.AddField(
            model_name='course',
            name='timings',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RenameField(
            model_name='participant',
            old_name='is_adviser_approved',
            new_name='is_adviser_reviewed',
        ),
        migrations.RenameField(
            model_name='participant',
            old_name='is_instructor_approved',
            new_name='is_instructor_reviewed',
        ),
        migrations.AddField(
            model_name='course',
            name='new_credits',
            field=models.CharField(default='', max_length=100, verbose_name='Credits (ex: 3:0)'),
        ),
        migrations.AddField(
            model_name='course',
            name='new_term',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='coursereg.Term'),
        ),
        migrations.AddField(
            model_name='course',
            name='should_count_towards_cgpa',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='participant',
            name='lock_from_student',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='participant',
            name='is_drop',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='participant',
            name='should_count_towards_cgpa',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='participant',
            name='registration_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coursereg.RegistrationType'),
        ),
        migrations.AddField(
            model_name='participant',
            name='new_grade',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coursereg.Grade'),
        ),
        migrations.AddField(
            model_name='participant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='participant',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='degree',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_dcc_sent_notification',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='department',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='department',
            name='abbreviation',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
    ]
