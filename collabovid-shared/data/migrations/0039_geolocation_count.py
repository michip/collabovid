# Generated by Django 3.0.7 on 2020-06-15 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0038_auto_20200615_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='geolocation',
            name='count',
            field=models.IntegerField(default=0),
        ),
    ]
