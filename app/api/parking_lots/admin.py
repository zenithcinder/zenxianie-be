from django.contrib import admin
from .models import ParkingLot, ParkingSpace

# Register your models here.
admin.site.register(ParkingLot)
admin.site.register(ParkingSpace)
