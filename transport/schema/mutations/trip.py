import graphene
from django.utils import timezone
from django.contrib.auth import get_user_model
from graphql import GraphQLError
from ...models import Trip, Bus, Route
from ..types import TripType
from ..permissions import check_role_permission

User = get_user_model()


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

        try:
            route = Route.objects.get(pk=route_id)
        except Route.DoesNotExist:
            raise GraphQLError("Route not found.")

        try:
            bus = Bus.objects.get(pk=bus_id)
        except Bus.DoesNotExist:
            raise GraphQLError("Bus not found.")

        if available_seats > bus.capacity or available_seats < 1:
            raise GraphQLError("Available seats must be between 1 and bus capacity.")

        if departure_time < timezone.now():
            raise GraphQLError("Departure time cannot be in the past.")

        try:
            organizer = User.objects.get(pk=organizer_id)
        except User.DoesNotExist:
            raise GraphQLError("Organizer not found.")

        try:
            driver = User.objects.get(pk=driver_id)
        except User.DoesNotExist:
            raise GraphQLError("Driver not found.")

        trip = Trip.objects.create(
            route=route,
            bus=bus,
            organizer=organizer,
            driver=driver,
            departure_time=departure_time,
            available_seats=available_seats
        )

        if crew_ids:
            crew_members = User.objects.filter(pk__in=crew_ids)
            if crew_members.count() != len(crew_ids):
                raise GraphQLError("One or more crew members not found.")
            trip.crew.set(crew_members)

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

        try:
            trip = Trip.objects.get(pk=id)
        except Trip.DoesNotExist:
            raise GraphQLError("Trip not found.")

        if bus_id is not None:
            try:
                bus = Bus.objects.get(pk=bus_id)
                trip.bus = bus
            except Bus.DoesNotExist:
                raise GraphQLError("Bus not found.")

        if driver_id is not None:
            try:
                driver = User.objects.get(pk=driver_id)
                trip.driver = driver
            except User.DoesNotExist:
                raise GraphQLError("Driver not found.")

        if crew_ids is not None:
            crew_members = User.objects.filter(pk__in=crew_ids)
            if crew_members.count() != len(crew_ids):
                raise GraphQLError("One or more crew members not found.")
            trip.crew.set(crew_members)

        if departure_time is not None:
            if departure_time < timezone.now():
                raise GraphQLError("Departure time cannot be in the past.")
            trip.departure_time = departure_time

        if available_seats is not None:
            if trip.bus and (available_seats > trip.bus.capacity or available_seats < 1):
                raise GraphQLError("Available seats must be between 1 and bus capacity.")
            trip.available_seats = available_seats

        trip.save()
        return UpdateTrip(trip=trip)


class DeleteTrip(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['organizer', 'manager'])
    def mutate(self, info, id):
        try:
            trip = Trip.objects.get(pk=id)
        except Trip.DoesNotExist:
            raise GraphQLError("Trip not found.")

        trip.delete()
        return DeleteTrip(ok=True)
