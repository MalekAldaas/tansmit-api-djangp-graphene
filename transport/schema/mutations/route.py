import graphene
from graphql import GraphQLError
from ...models import Route, Branch
from ..types import RouteType
from ..permissions import check_role_permission
from datetime import timedelta

def parse_duration_string(duration_str):
    try:
        hours, minutes, seconds = map(int, duration_str.split(":"))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except ValueError:
        raise GraphQLError("Invalid duration format. Use HH:MM:SS.")


class CreateRoute(graphene.Mutation):
    route = graphene.Field(RouteType)

    class Arguments:
        origin_id = graphene.ID(required=True)
        destination_id = graphene.ID(required=True)
        duration = graphene.String(required=True)
        distance_km = graphene.Float(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, origin_id, destination_id, duration, distance_km):
        try:
            origin = Branch.objects.get(pk=origin_id)
            destination = Branch.objects.get(pk=destination_id)
        except Branch.DoesNotExist:
            raise GraphQLError("One or both branches not found.")

        if origin.id == destination.id:
            raise GraphQLError("Origin and destination cannot be the same branch.")
        
        duration = parse_duration_string(duration)
        route = Route.objects.create(
            origin=origin,
            destination=destination,
            duration=duration,
            distance_km=distance_km
        )
        return CreateRoute(route=route)


class UpdateRoute(graphene.Mutation):
    route = graphene.Field(RouteType)

    class Arguments:
        id = graphene.ID(required=True)
        origin_id = graphene.ID()
        destination_id = graphene.ID()
        duration = graphene.String(required=True)
        distance_km = graphene.Float()

    @check_role_permission(['manager'])
    def mutate(self, info, id, **kwargs):
        try:
            route = Route.objects.get(pk=id)
        except Route.DoesNotExist:
            raise GraphQLError("Route not found.")

        if 'origin_id' in kwargs:
            try:
                route.origin = Branch.objects.get(pk=kwargs.pop('origin_id'))
            except Branch.DoesNotExist:
                raise GraphQLError("Origin branch not found.")

        if 'destination_id' in kwargs:
            try:
                route.destination = Branch.objects.get(pk=kwargs.pop('destination_id'))
            except Branch.DoesNotExist:
                raise GraphQLError("Destination branch not found.")

        if 'duration' in kwargs:
            duration_str = kwargs.pop('duration')
            route.duration = parse_duration_string(duration_str)

        for attr, value in kwargs.items():
            setattr(route, attr, value)

        if route.origin_id == route.destination_id:
            raise GraphQLError("Origin and destination cannot be the same.")

        
        route.save()
        return UpdateRoute(route=route)


class DeleteRoute(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        deleted, _ = Route.objects.filter(pk=id).delete()
        if deleted == 0:
            raise GraphQLError("Route not found or already deleted.")
        return DeleteRoute(ok=True)
