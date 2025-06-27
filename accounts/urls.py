from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterUserView, ChangePasswordView, UpdateUserView, ChangeUserGroupView


app_name = 'accounts'

urlpatterns = [
    path('', include('djoser.urls')),
    path('jwt/create/', TokenObtainPairView.as_view(), name='jwt-create'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    path('register/', RegisterUserView.as_view(), name='register'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('update-account/', UpdateUserView.as_view(), name='update-account'),
    path('change-group/', ChangeUserGroupView.as_view(), name='change-group')
]
