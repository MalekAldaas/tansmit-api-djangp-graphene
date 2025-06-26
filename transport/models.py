from django.db import models
from django.contrib.auth.models import AbstractUser



class CustomUser(AbstractUser):
    email = models.EmailField(blank=False, max_length=255, verbose_name='email')
    USERNAME_FIELD = "username"
    EMAIL_FIELD = 'email'

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='branches')

    def __str__(self):
        return f"{self.name} - {self.city.name}"

# ---- Transportation Models ----
class Bus(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='buses')

    def __str__(self):
        return self.plate_number

class Route(models.Model):
    origin = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='routes_to')
    duration = models.DurationField()
    distance_km = models.FloatField()

    def __str__(self):
        return f"{self.origin} to {self.destination}"

class Trip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='trips')
    organizer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='organized_trips')
    driver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='driven_trips')
    crew = models.ManyToManyField(CustomUser, related_name='crewed_trips', blank=True)
    departure_time = models.DateTimeField()
    available_seats = models.PositiveIntegerField()

    def __str__(self):
        return f"Trip from {self.route.origin} to {self.route.destination} at {self.departure_time}"

class Booking(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    seat_number = models.PositiveIntegerField()
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'seat_number')

    def __str__(self):
        return f"{self.customer.username} - Seat {self.seat_number} on {self.trip}"
