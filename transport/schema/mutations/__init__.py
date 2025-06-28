import graphene
from .city import CreateCity, UpdateCity, DeleteCity
from .branch import CreateBranch, UpdateBranch, DeleteBranch
from .bus import CreateBus, UpdateBus, DeleteBus
from .route import CreateRoute, UpdateRoute, DeleteRoute
from .trip import CreateTrip, UpdateTrip, DeleteTrip
from .booking import CreateBooking, DeleteBooking


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

