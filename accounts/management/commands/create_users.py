from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create multiple sample users and assign them to groups"

    def handle(self, *args, **kwargs):
        group_names = ["admin", "manager", "delivery crew", "customer"]

        # Ensure groups exist
        for group_name in group_names:
            Group.objects.get_or_create(name=group_name)

        user_counter = {
            "admin": 1,
            "manager": 1,
            "delivery crew": 1,
            "customer": 1
        }

        for group in group_names:
            for i in range(10):
                username = f"{group.replace(' ', '')}{user_counter[group]}"
                email = f"{username}@example.com"
                password = f"{group.replace(' ', '')}123"

                # Check if user with same username or email exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(f"User already exists: {username}")
                    continue
                if User.objects.filter(email=email).exists():
                    self.stdout.write(f"Email already exists: {email}")
                    continue

                # Create the user
                user = User(username=username, email=email)
                user.set_password(password)
                user.save()
                group_obj = Group.objects.get(name=group)
                user.groups.add(group_obj)

                self.stdout.write(self.style.SUCCESS(
                    f"Created user: {username} | Group: {group} | Email: {email}"
                ))

                user_counter[group] += 1
