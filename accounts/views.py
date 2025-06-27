from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import (
    UserRegistrationSerializer,
    UserUpdateSerializer,
    PasswordUpdateSerializer,
    ChangeUserGroupSerializer
)
from rest_framework.views import APIView
from .permissions import IsManager


class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UpdateUserView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = PasswordUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password updated successfully'}, status=status.HTTP_200_OK)


class ChangeUserGroupView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request):
        serializer = ChangeUserGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'User group updated successfully'}, status=status.HTTP_200_OK)
