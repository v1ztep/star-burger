# Generated by Django 3.2 on 2022-02-01 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0046_auto_20220128_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('RAW', 'Необработанный'), ('FINISHED', 'Обработанный')], db_index=True, default='RAW', max_length=8, verbose_name='статус'),
        ),
    ]