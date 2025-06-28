from functools import wraps
from graphql import GraphQLError

def check_role_permission(allowed_roles):
    """
    Decorator to restrict access based on user group roles.

    Args:
        allowed_roles (list[str]): List of role names allowed to perform the action.
    """
    def decorator(resolver_func):
        @wraps(resolver_func)
        def wrapper(self, info, *args, **kwargs):
            user = info.context.user

            if not user.is_authenticated:
                raise GraphQLError("Authentication required.")

            # Manager is always allowed
            if user.groups.filter(name__iexact="manager").exists():
                return resolver_func(self, info, *args, **kwargs)

            user_groups = [group.name.lower() for group in user.groups.all()]
            allowed_roles_lower = [role.lower() for role in allowed_roles]

            if not user_groups and "customer" in allowed_roles_lower:
                return resolver_func(self, info, *args, **kwargs)

            if any(role in allowed_roles_lower for role in user_groups):
                return resolver_func(self, info, *args, **kwargs)

            raise GraphQLError("You do not have permission to perform this action.")

        return wrapper

    return decorator
