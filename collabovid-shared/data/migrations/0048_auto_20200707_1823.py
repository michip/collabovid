# Generated by Django 3.0.7 on 2020-07-07 18:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0047_scrapeconflict'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorNameResolution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_first_name', models.TextField(max_length=50)),
                ('source_last_name', models.TextField(max_length=50)),
            ],
        ),
        migrations.AddIndex(
            model_name='author',
            index=models.Index(fields=['last_name', 'first_name'], name='data_author_last_na_d01e12_idx'),
        ),
        migrations.AddField(
            model_name='authornameresolution',
            name='target_author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.Author'),
        ),
        migrations.AddIndex(
            model_name='authornameresolution',
            index=models.Index(fields=['source_last_name', 'source_first_name'], name='data_author_source__2ad6dc_idx'),
        ),
    ]
