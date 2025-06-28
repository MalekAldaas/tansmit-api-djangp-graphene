import graphene
from graphql import GraphQLError
from ...models import Bus, Branch
from ..types import BusType
from ..permissions import check_role_permission


class CreateBus(graphene.Mutation):
    bus = graphene.Field(BusType)

    class Arguments:
        plate_number = graphene.String(required=True)
        capacity = graphene.Int(required=True)
        branch_id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, plate_number, capacity, branch_id):
        if Bus.objects.filter(plate_number__iexact=plate_number).exists():
            raise GraphQLError("A bus with this plate number already exists.")

        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            raise GraphQLError("Branch not found.")

        bus = Bus.objects.create(
            plate_number=plate_number,
            capacity=capacity,
            branch=branch
        )
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
        try:
            bus = Bus.objects.get(pk=id)
        except Bus.DoesNotExist:
            raise GraphQLError("Bus not found.")

        if plate_number:
            if Bus.objects.exclude(pk=id).filter(plate_number__iexact=plate_number).exists():
                raise GraphQLError("Another bus with this plate number already exists.")
            bus.plate_number = plate_number

        if capacity is not None:
            bus.capacity = capacity

        if branch_id:
            try:
                branch = Branch.objects.get(pk=branch_id)
            except Branch.DoesNotExist:
                raise GraphQLError("Branch not found.")
            bus.branch = branch

        bus.save()
        return UpdateBus(bus=bus)

class DeleteBus(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        try:
            bus = Bus.objects.get(pk=id)
        except Bus.DoesNotExist:
            raise GraphQLError("Bus not found.")
        bus.delete()
        return DeleteBus(ok=True)
