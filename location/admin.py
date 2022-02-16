from django.contrib import admin

from location.models import DeliveryLocation


@admin.register(DeliveryLocation)
class DeliveryLocation(admin.ModelAdmin):
    list_display = ['address', 'lon', 'lat']
