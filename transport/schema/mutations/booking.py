import graphene
from graphql import GraphQLError
from django.utils import timezone
from ...models import Booking, Trip
from ..types import BookingType
from ..permissions import check_role_permission


class CreateBooking(graphene.Mutation):
    booking = graphene.Field(BookingType)

    class Arguments:
        trip_id = graphene.ID(required=True)
        seat_number = graphene.Int(required=True)

    @check_role_permission(['customer'])
    def mutate(self, info, trip_id, seat_number):
        user = info.context.user

        try:
            trip = Trip.objects.select_related('bus').get(pk=trip_id)
        except Trip.DoesNotExist:
            raise GraphQLError("Trip not found.")

        if trip.departure_time < timezone.now():
            raise GraphQLError("You cannot book a past trip.")

        if trip.bus is None:
            raise GraphQLError("Trip does not have an assigned bus yet.")

        if seat_number < 1 or seat_number > trip.bus.capacity:
            raise GraphQLError("Invalid seat number.")

        if Booking.objects.filter(trip=trip, seat_number=seat_number).exists():
            raise GraphQLError("Seat already booked.")

        if trip.available_seats <= 0:
            raise GraphQLError("No available seats on this trip.")

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
        user = info.context.user

        try:
            booking = Booking.objects.select_related('trip').get(pk=id)
        except Booking.DoesNotExist:
            raise GraphQLError("Booking not found.")

        if booking.customer != user:
            raise GraphQLError("You can only delete your own bookings.")

        # Restore seat
        if booking.trip:
            booking.trip.available_seats += 1
            booking.trip.save()

        booking.delete()
        return DeleteBooking(ok=True)
