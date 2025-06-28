import graphene
from graphql import GraphQLError
from ...models import Branch, City
from ..types import BranchType
from ..permissions import check_role_permission


class CreateBranch(graphene.Mutation):
    branch = graphene.Field(BranchType)

    class Arguments:
        name = graphene.String(required=True)
        city_id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, name, city_id):
        try:
            city = City.objects.get(pk=city_id)
        except City.DoesNotExist:
            raise GraphQLError("City not found.")

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
        try:
            branch = Branch.objects.get(pk=id)
        except Branch.DoesNotExist:
            raise GraphQLError("Branch not found.")

        if name is not None:
            branch.name = name
        if city_id is not None:
            try:
                city = City.objects.get(pk=city_id)
                branch.city = city
            except City.DoesNotExist:
                raise GraphQLError("City not found.")

        branch.save()
        return UpdateBranch(branch=branch)


class DeleteBranch(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        id = graphene.ID(required=True)

    @check_role_permission(['manager'])
    def mutate(self, info, id):
        try:
            branch = Branch.objects.get(pk=id)
            branch.delete()
            return DeleteBranch(ok=True)
        except Branch.DoesNotExist:
            raise GraphQLError("Branch not found.")
