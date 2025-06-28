import graphene
from graphql import GraphQLError
from django.utils import timezone
from ..models import City, Branch, Bus, Route, Trip, Booking
from .types import CityType, BranchType, BusType, RouteType, TripType, BookingType
from .permissions import check_role_permission
from django.db.models import Q


class Query(graphene.ObjectType):
    # === CITY ===
    all_cities = graphene.List(CityType)
    city = graphene.Field(CityType, id=graphene.ID(required=True))

    @check_role_permission(['manager', 'organizer'])
    def resolve_all_cities(self, info):
        return City.objects.all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_city(self, info, id):
        return City.objects.get(pk=id)

    # === BRANCH ===
    all_branches = graphene.List(BranchType)
    branch = graphene.Field(BranchType, id=graphene.ID(required=True))

    @check_role_permission(['manager', 'organizer'])
    def resolve_all_branches(self, info):
        return Branch.objects.select_related('city').all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_branch(self, info, id):
        return Branch.objects.get(pk=id)

    # === BUS ===
    all_buses = graphene.List(BusType)
    bus = graphene.Field(BusType, id=graphene.ID(required=True))

    @check_role_permission(['manager'])
    def resolve_all_buses(self, info):
        return Bus.objects.select_related('branch').all()

    @check_role_permission(['manager'])
    def resolve_bus(self, info, id):
        return Bus.objects.get(pk=id)

    # === ROUTE ===
    all_routes = graphene.List(RouteType)
    route = graphene.Field(RouteType, id=graphene.ID(required=True))

    @check_role_permission(['manager', 'organizer'])
    def resolve_all_routes(self, info):
        return Route.objects.select_related('origin', 'destination').all()

    @check_role_permission(['manager', 'organizer'])
    def resolve_route(self, info, id):
        return Route.objects.get(pk=id)

    # === TRIP ===
    all_trips = graphene.List(TripType)
    trip = graphene.Field(TripType, id=graphene.ID(required=True))

    @check_role_permission(['manager', 'organizer', 'customer', 'driver', 'crew'])
    def resolve_all_trips(self, info):
        user = info.context.user
        user_groups = {g.name.lower() for g in user.groups.all()}
        now = timezone.now()

        queryset = Trip.objects.select_related(
            'route', 'bus', 'organizer', 'driver'
        ).prefetch_related('crew').order_by('-departure_time')

        if 'customer' in user_groups:
            return queryset.filter(
                departure_time__gte=now,
                available_seats__gt=0
            )

        if 'driver' in user_groups or 'crew' in user_groups:
            return queryset.filter(Q(driver=user) | Q(crew__in=[user]))

        return queryset
    
    @check_role_permission(['manager', 'organizer', 'customer', 'driver', 'crew'])
    def resolve_trip(self, info, id):
        trip = Trip.objects.select_related(
            'route', 'bus', 'organizer', 'driver'
        ).prefetch_related('crew').get(pk=id)
        
        user = info.context.user
        user_groups = {g.name.lower() for g in user.groups.all()}

        if 'customer' in user_groups and (
            trip.departure_time < timezone.now()
            or trip.available_seats <= 0
        ):
            raise GraphQLError("You are not allowed to view this trip.")
        
        if ('driver' in user_groups or 'crew' in user_groups) and \
        (trip.driver != user and user not in trip.crew.all() and trip.organizer != user):
            raise GraphQLError("You are not allowed to view this trip.")
            
        return trip

    # === CUSTOMER BOOKINGS ===
    my_bookings = graphene.List(BookingType)
    all_bookings = graphene.List(BookingType)
    booking = graphene.Field(BookingType, id=graphene.ID(required=True))
    customer_bookings = graphene.List(
        BookingType,
        customer_id=graphene.ID(required=True)
    )

    @check_role_permission(['customer'])
    def resolve_my_bookings(self, info):
        user = info.context.user
        return Booking.objects.filter(
            customer=user
        ).select_related('trip').order_by('-booked_at')

    @check_role_permission(['manager', 'organizer'])
    def resolve_all_bookings(self, info):
        return Booking.objects.all().select_related(
            'trip', 'customer'
        ).order_by('-booked_at')

    @check_role_permission(['manager', 'organizer', 'customer'])
    def resolve_booking(self, info, id):
        user = info.context.user
        booking = Booking.objects.select_related(
            'trip', 'customer'
        ).get(pk=id)
        
        # Customers can only see their own bookings
        if 'customer' in [g.name.lower() for g in user.groups.all()]:
            if booking.customer != user:
                raise GraphQLError("You can only view your own bookings")
        
        return booking

    @check_role_permission(['manager', 'organizer'])
    def resolve_customer_bookings(self, info, customer_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        customer = User.objects.get(pk=customer_id)
        return Booking.objects.filter(
            customer=customer
        ).select_related('trip').order_by('-booked_at')

