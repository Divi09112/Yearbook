# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-10 13:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auto_20180410_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='department',
            field=models.CharField(choices=[('biotechnology', 'biotechnology'), ('chemical', 'chemical'), ('civil', 'civil'), ('computer', 'computer'), ('electrical', 'electrical'), ('mathematics', 'mathematics'), ('mechanical', 'mechanical'), ('physics', 'physics'), ('textile', 'textile')], max_length=100),
        ),
    ]
