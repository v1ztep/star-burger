# Generated by Django 3.2 on 2022-02-01 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0049_auto_20220201_0516'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('Cash', 'Наличными'), ('Card', 'По карте')], db_index=True, default='Не заполнено', max_length=4, verbose_name='способ оплаты'),
        ),
    ]
