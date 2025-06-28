from django.contrib import admin
from .models import Route, Bus, City, Trip, Booking, Branch

# Register your models here.
admin.site.register(Route)
admin.site.register(Bus)
admin.site.register(City)   
admin.site.register(Trip)        
admin.site.register(Booking)        
admin.site.register(Branch)             