import graphene
from graphene_django import DjangoObjectType
from ..models import City, Branch, Bus, Route, Trip, Booking
from django.contrib.auth import get_user_model

User = get_user_model()

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email")  # expose as needed

class CityType(DjangoObjectType):
    class Meta:
        model = City
        fields = ("id", "name")


class BranchType(DjangoObjectType):
    class Meta:
        model = Branch
        fields = ("id", "name", "city")


class BusType(DjangoObjectType):
    class Meta:
        model = Bus
        fields = ("id", "plate_number", "capacity", "branch")


class RouteType(DjangoObjectType):
    duration = graphene.String()
    class Meta:
        model = Route
        fields = ("id", "origin", "destination", "duration", "distance_km")
    
    def resolve_duration(self, info):
        total_seconds = int(self.duration.total_seconds())
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    

class BookingType(DjangoObjectType):
    class Meta:
        model = Booking
        fields = ("id", "customer", "trip", "seat_number", "booked_at")


class TripType(DjangoObjectType):
    organizer = graphene.Field(UserType)
    driver    = graphene.Field(UserType)
    crew      = graphene.List(UserType)
    bookings  = graphene.List(lambda: BookingType)
    available_seat_numbers = graphene.List(graphene.Int)
    
    
    class Meta:
        model = Trip
        fields = (
            "id", "route", "bus",
            "departure_time", "available_seats", "bookings"
        )

    def resolve_organizer(self, info):
        return self.organizer

    def resolve_driver(self, info):
        return self.driver

    def resolve_crew(self, info):
        return self.crew.all()

    def resolve_bookings(self, info):
        return self.bookings.all()

    def resolve_available_seat_numbers(self, info):
        all_seats = set(range(1, self.bus.capacity + 1))
        booked   = set(self.bookings.values_list("seat_number", flat=True))
        return sorted(all_seats - booked)

    def resolve_bookings(self, info):
        return self.bookings.all()

    def resolve_available_seat_numbers(self, info):
        all_seats = set(range(1, self.bus.capacity + 1))
        booked_seats = set(self.bookings.values_list("seat_number", flat=True))
        return sorted(all_seats - booked_seats)

