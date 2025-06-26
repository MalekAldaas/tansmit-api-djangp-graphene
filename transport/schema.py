import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import City, Branch, Bus, Route, Trip, Booking
from .permissions import check_role_permission

User = get_user_model()

# ---------------- OBJECT TYPES ----------------
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
    class Meta:
        model = Route
        fields = ("id", "origin", "destination", "duration", "distance_km")

class TripType(DjangoObjectType):
    bookings = graphene.List(lambda: BookingType)
    available_seat_numbers = graphene.List(graphene.Int)
    

    class Meta:
        model = Trip
        fields = ("id", "route", "bus", "organizer", "driver", "crew", "departure_time", "available_seats", "bookings")

    def resolve_bookings(self, info):
        return self.bookings.all()

    def resolve_available_seat_numbers(self, info):
        all_seats = set(range(1, self.bus.capacity + 1))
        booked_seats = set(self.bookings.values_list("seat_number", flat=True))
        return sorted(all_seats - booked_seats)

class BookingType(DjangoObjectType):
    class Meta:
        model = Booking
        fields = ("id", "customer", "trip", "seat_number", "booked_at")

# ---------------- QUERIES ----------------
class Query(graphene.ObjectType):
    # === CITY ===
    @check_role_permission(['manager', 'organizer'])
    def resolve_all_cities(self, info):
        return City.objects.all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_city(self, info, id):
        return City.objects.get(pk=id)

    # === BRANCH ===
    @check_role_permission(['manager', 'organizer'])
    def resolve_all_branches(self, info):
        return Branch.objects.select_related('city').all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_branch(self, info, id):
        return Branch.objects.get(pk=id)

    # === BUS ===
    @check_role_permission(['manager'])
    def resolve_all_buses(self, info):
        return Bus.objects.select_related('branch').all()

    @check_role_permission(['manager'])
    def resolve_bus(self, info, id):
        return Bus.objects.get(pk=id)

    # === ROUTE ===
    @check_role_permission(['manager', 'organizer'])
    def resolve_all_routes(self, info):
        return Route.objects.select_related('origin', 'destination').all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_route(self, info, id):
        return Route.objects.get(pk=id)

    # === TRIP ===
    @check_role_permission(['manager', 'organizer', 'customer'])
    def resolve_all_trips(self, info):
        user = info.context.user

        # Customers see only future available trips
        if 'customer' in [g.name.lower() for g in user.groups.all()]:
            return Trip.objects.filter(departure_time__gte= timezone.now(), available_seats__gt=0)\
                               .select_related('route', 'bus', 'organizer', 'driver')\
                               .prefetch_related('crew')
        
        # Organizers and managers see everything
        return Trip.objects.select_related('route', 'bus', 'organizer', 'driver')\
                           .prefetch_related('crew')

    @check_role_permission(['manager', 'organizer', 'customer'])
    def resolve_trip(self, info, id):
        trip = Trip.objects.select_related('route', 'bus', 'organizer', 'driver').get(pk=id)

        user = info.context.user
        groups = [g.name.lower() for g in user.groups.all()]
        if 'customer' in groups and (trip.departure_time < timezone.now() or trip.available_seats <= 0):
            raise GraphQLError("You are not allowed to view this trip.")
        
        return trip

    # === CUSTOMER BOOKINGS ===
    @check_role_permission(['customer'])
    def resolve_my_bookings(self, info):
        user = info.context.user
        return Booking.objects.filter(customer=user).select_related('trip')
    
    


# ---------------- MUTATIONS ----------------
# CITY CRUD
class CreateCity(graphene.Mutation):
    city = graphene.Field(CityType)

    class Arguments:
        name = graphene.String(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, name):
        city = City.objects.create(name=name)
        return CreateCity(city=city)

class UpdateCity(graphene.Mutation):
    city = graphene.Field(CityType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()

    @check_role_permission(['manager'])
    def mutate(self, info, id, name=None):
        city = City.objects.get(pk=id)
        if name is not None:
            city.name = name
            city.save()
        return UpdateCity(city=city)

class DeleteCity(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        City.objects.filter(pk=id).delete()
        return DeleteCity(ok=True)

# BRANCH CRUD
class CreateBranch(graphene.Mutation):
    branch = graphene.Field(BranchType)

    class Arguments:
        name = graphene.String(required=True)
        city_id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, name, city_id):
        from .models import City
        city = City.objects.get(pk=city_id)
        branch = Branch.objects.create(name=name, city=city)
        return CreateBranch(branch=branch)

class UpdateBranch(graphene.Mutation):
    branch = graphene.Field(BranchType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        city_id = graphene.ID()

    @check_role_permission(['manager'])
    def mutate(self, info, id, name=None, city_id=None):
        branch = Branch.objects.get(pk=id)
        if name is not None:
            branch.name = name
        if city_id is not None:
            from .models import City
            branch.city = City.objects.get(pk=city_id)
        branch.save()
        return UpdateBranch(branch=branch)

class DeleteBranch(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        Branch.objects.filter(pk=id).delete()
        return DeleteBranch(ok=True)

# BUS CRUD
class CreateBus(graphene.Mutation):
    bus = graphene.Field(BusType)

    class Arguments:
        plate_number = graphene.String(required=True)
        capacity = graphene.Int(required=True)
        branch_id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, plate_number, capacity, branch_id):
        branch = Branch.objects.get(pk=branch_id)
        bus = Bus.objects.create(plate_number=plate_number, capacity=capacity, branch=branch)
        return CreateBus(bus=bus)

class UpdateBus(graphene.Mutation):
    bus = graphene.Field(BusType)

    class Arguments:
        id = graphene.ID(required=True)
        plate_number = graphene.String()
        capacity = graphene.Int()
        branch_id = graphene.ID()

    @check_role_permission(['manager'])
    def mutate(self, info, id, plate_number=None, capacity=None, branch_id=None):
        bus = Bus.objects.get(pk=id)
        if plate_number is not None:
            bus.plate_number = plate_number
        if capacity is not None:
            bus.capacity = capacity
        if branch_id is not None:
            bus.branch = Branch.objects.get(pk=branch_id)
        bus.save()
        return UpdateBus(bus=bus)

class DeleteBus(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        Bus.objects.filter(pk=id).delete()
        return DeleteBus(ok=True)

# ROUTE CRUD
class CreateRoute(graphene.Mutation):
    route = graphene.Field(RouteType)

    class Arguments:
        origin_id = graphene.ID(required=True)
        destination_id = graphene.ID(required=True)
        duration = graphene.String(required=True)
        distance_km = graphene.Float(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, origin_id, destination_id, duration, distance_km):
        origin = Branch.objects.get(pk=origin_id)
        destination = Branch.objects.get(pk=destination_id)
        route = Route.objects.create(origin=origin, destination=destination,
                                     duration=duration, distance_km=distance_km)
        return CreateRoute(route=route)

class UpdateRoute(graphene.Mutation):
    route = graphene.Field(RouteType)

    class Arguments:
        id = graphene.ID(required=True)
        origin_id = graphene.ID()
        destination_id = graphene.ID()
        duration = graphene.String()
        distance_km = graphene.Float()

    @check_role_permission(['manager'])
    def mutate(self, info, id, **kwargs):
        route = Route.objects.get(pk=id)
        if 'origin_id' in kwargs:
            route.origin = Branch.objects.get(pk=kwargs.pop('origin_id'))
        if 'destination_id' in kwargs:
            route.destination = Branch.objects.get(pk=kwargs.pop('destination_id'))
        for attr, value in kwargs.items():
            setattr(route, attr, value)
        route.save()
        return UpdateRoute(route=route)

class DeleteRoute(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        Route.objects.filter(pk=id).delete()
        return DeleteRoute(ok=True)


# TRIP CRUD
class CreateTrip(graphene.Mutation):
    trip = graphene.Field(TripType)

    class Arguments:
        route_id = graphene.ID(required=True)
        bus_id = graphene.ID(required=True)
        organizer_id = graphene.ID(required=True)
        driver_id = graphene.ID(required=True)
        crew_ids = graphene.List(graphene.ID)
        departure_time = graphene.DateTime(required=True)
        available_seats = graphene.Int(required=True)

    @check_role_permission(['organizer', 'manager'])
    def mutate(self, info, route_id, bus_id, organizer_id,
               driver_id, crew_ids=None, departure_time=None, available_seats=None):
        route = Route.objects.get(pk=route_id)
        bus = Bus.objects.get(pk=bus_id)
        organizer = settings.User.objects.get(pk=organizer_id)
        driver = settings.User.objects.get(pk=driver_id)
        trip = Trip.objects.create(
            route=route, bus=bus, organizer=organizer,
            driver=driver, departure_time=departure_time,
            available_seats=available_seats
        )
        if crew_ids:
            trip.crew.set(settings.User.objects.filter(pk__in=crew_ids))
        return CreateTrip(trip=trip)

class UpdateTrip(graphene.Mutation):
    trip = graphene.Field(TripType)

    class Arguments:
        id = graphene.ID(required=True)
        bus_id = graphene.ID()
        driver_id = graphene.ID()
        crew_ids = graphene.List(graphene.ID)
        departure_time = graphene.DateTime()
        available_seats = graphene.Int()

    @check_role_permission(['organizer', 'manager'])
    def mutate(self, info, id, bus_id=None, driver_id=None, crew_ids=None, departure_time=None, available_seats=None):
        trip = Trip.objects.get(pk=id)
        if bus_id is not None:
            trip.bus = Bus.objects.get(pk=bus_id)
        if driver_id is not None:
            trip.driver = settings.User.objects.get(pk=driver_id)
        if crew_ids is not None:
            trip.crew.set(settings.User.objects.filter(pk__in=crew_ids))
        if departure_time is not None:
            trip.departure_time = departure_time
        if available_seats is not None:
            trip.available_seats = available_seats
        trip.save()
        return UpdateTrip(trip=trip)

class DeleteTrip(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['organizer', 'manager'])
    def mutate(self, info, id):
        Trip.objects.filter(pk=id).delete()
        return DeleteTrip(ok=True)


# BOOKING CRUD
class CreateBooking(graphene.Mutation):
    booking = graphene.Field(BookingType)

    class Arguments:
        trip_id = graphene.ID(required=True)
        seat_number = graphene.Int(required=True)

    @check_role_permission(['customer'])
    def mutate(self, info, trip_id, seat_number):
        user = info.context.user
        trip = Trip.objects.get(pk=trip_id)
        if seat_number > trip.available_seats or seat_number < 1:
            raise GraphQLError("Invalid seat number")
        if Booking.objects.filter(trip=trip, seat_number=seat_number).exists():
            raise GraphQLError("Seat already booked")
        booking = Booking.objects.create(
            customer=user,
            trip=trip,
            seat_number=seat_number,
            booked_at=timezone.now()
        )
        trip.available_seats -= 1
        trip.save()
        return CreateBooking(booking=booking)

class DeleteBooking(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['customer'])
    def mutate(self, info, id):
        booking = Booking.objects.get(pk=id)
        user = info.context.user
        if booking.customer != user:
            raise GraphQLError("Not your booking to cancel")
        trip = booking.trip
        booking.delete()
        trip.available_seats += 1
        trip.save()
        return DeleteBooking(ok=True)


# ---------------- SCHEMA ----------------
class Mutation(graphene.ObjectType):
    # City
    create_city = CreateCity.Field()
    update_city = UpdateCity.Field()
    delete_city = DeleteCity.Field()

    # Branch
    create_branch = CreateBranch.Field()
    update_branch = UpdateBranch.Field()
    delete_branch = DeleteBranch.Field()

    # Bus
    create_bus = CreateBus.Field()
    update_bus = UpdateBus.Field()
    delete_bus = DeleteBus.Field()

    # Route
    create_route = CreateRoute.Field()
    update_route = UpdateRoute.Field()
    delete_route = DeleteRoute.Field()

    # Trip
    create_trip = CreateTrip.Field()
    update_trip = UpdateTrip.Field()
    delete_trip = DeleteTrip.Field()

    # Booking
    create_booking = CreateBooking.Field()
    delete_booking = DeleteBooking.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)