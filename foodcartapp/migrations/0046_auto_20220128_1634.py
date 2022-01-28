# Generated by Django 3.2 on 2022-01-28 13:34
from decimal import Decimal

from django.db import migrations


def calculate_price_for_old_orders(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    order_items_without_price = OrderItem.objects.filter(total_price=0)
    for order_item in order_items_without_price.iterator():
        order_item.total_price = Decimal(order_item.product.price * order_item.quantity)
        order_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0045_alter_orderitem_total_price'),
    ]

    operations = [
        migrations.RunPython(calculate_price_for_old_orders),
    ]