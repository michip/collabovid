# Generated by Django 3.0.7 on 2020-07-07 15:59

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0046_auto_20200706_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapeConflict',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datapoint', django.contrib.postgres.fields.jsonb.JSONField()),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Paper')),
            ],
        ),
    ]
