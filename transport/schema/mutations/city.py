import graphene
from graphql import GraphQLError
from ...models import City
from ..types import CityType
from ..permissions import check_role_permission


class CreateCity(graphene.Mutation):
    city = graphene.Field(CityType)

    class Arguments:
        name = graphene.String(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, name):
        if City.objects.filter(name__iexact=name).exists():
            raise GraphQLError("City with this name already exists.")
        city = City.objects.create(name=name)
        city.save()
        return CreateCity(city=city)


class UpdateCity(graphene.Mutation):
    city = graphene.Field(CityType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()

    @check_role_permission(['manager'])
    def mutate(self, info, id, name=None):
        try:
            city = City.objects.get(pk=id)
        except City.DoesNotExist:
            raise GraphQLError("City not found.")

        if name:
            if City.objects.exclude(pk=id).filter(name__iexact=name).exists():
                raise GraphQLError("Another city with this name already exists.")
            city.name = name
            city.save()

        return UpdateCity(city=city)


class DeleteCity(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        deleted_count, _ = City.objects.filter(pk=id).delete()
        if deleted_count == 0:
            raise GraphQLError("City not found.")
        return DeleteCity(ok=True)
