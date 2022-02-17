# Generated by Django 3.2 on 2022-02-16 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deliverylocation',
            name='lat',
            field=models.FloatField(blank=True, verbose_name='широта'),
        ),
        migrations.AlterField(
            model_name='deliverylocation',
            name='lon',
            field=models.FloatField(blank=True, verbose_name='долгота'),
        ),
    ]