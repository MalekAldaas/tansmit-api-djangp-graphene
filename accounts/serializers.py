from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.exceptions import ValidationError

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(slug_field='name', many=True, read_only=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'groups')
        

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        # Add to "customer" group by default
        customer_group, _ = Group.objects.get_or_create(name='customer')
        user.groups.add(customer_group)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise ValidationError({'old_password': 'Wrong password'})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ChangeUserGroupSerializer(serializers.Serializer):
    username = serializers.CharField()
    new_group = serializers.ChoiceField(choices=[
        ('manager', 'Manager'),
        ('organizer', 'Organizer'),
        ('driver', 'Driver'),
        ('crew', 'Crew'),
        ('customer', 'Customer')
    ])

    def validate(self, data):
        try:
            user = User.objects.get(username=data['username'])
            data['user'] = user
        except User.DoesNotExist:
            raise ValidationError({'username': 'User not found'})
        return data

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.groups.clear()
        group, _ = Group.objects.get_or_create(name=self.validated_data['new_group'])
        user.groups.add(group)
        return user
