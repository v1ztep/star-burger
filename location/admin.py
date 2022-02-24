from django.contrib import admin

from location.models import DeliveryLocation
from location.models import RestaurantLocation


@admin.register(DeliveryLocation)
class DeliveryLocation(admin.ModelAdmin):
    list_display = ['address', 'lon', 'lat']


@admin.register(RestaurantLocation)
class DeliveryLocation(admin.ModelAdmin):
    list_display = ['address', 'lon', 'lat']
