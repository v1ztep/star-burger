from django.db import models
from django.utils import timezone


class DeliveryLocation(models.Model):
    address = models.CharField(
        verbose_name='адрес доставки',
        max_length=200,
        unique=True
    )
    lon = models.FloatField('долгота', blank=True)
    lat = models.FloatField('широта', blank=True)
    registered_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='дата запроса к геокодеру',
        db_index=True
    )
