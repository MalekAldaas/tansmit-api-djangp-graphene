from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class AccountsTests(APITestCase):

    def setUp(self):
        self.manager_group, _ = Group.objects.get_or_create(name='manager')
        self.customer_group, _ = Group.objects.get_or_create(name='customer')

        self.manager = User.objects.create_user(username='manager', password='managerpass')
        self.manager.groups.add(self.manager_group)

        self.user = User.objects.create_user(username='user1', password='userpass', email='user1@g.com')
        self.user.groups.add(self.customer_group)

        self.manager_client = APIClient()
        self.manager_client.force_authenticate(user=self.manager)

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

    def test_user_registration_creates_customer_group(self):
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@g.com',
            'password': 'newpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.groups.filter(name='customer').exists())

    def test_user_update_own_profile(self):
        url = reverse('accounts:update-account')
        data = {
            'username': 'updateduser',
            'email': 'updated@g.com'
        }
        response = self.user_client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@g.com')

    def test_password_change_correct_old_password(self):
        url = reverse('accounts:change-password')
        data = {
            'old_password': 'userpass',
            'new_password': 'newstrongpass'
        }
        response = self.user_client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newstrongpass'))

    def test_password_change_incorrect_old_password(self):
        url = reverse('accounts:change-password')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newstrongpass'
        }
        response = self.user_client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_manager_can_change_user_group(self):
        url = reverse('accounts:change-group')
        data = {
            'username': self.user.username,
            'new_group': 'organizer'
        }
        response = self.manager_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.groups.filter(name='organizer').exists())
        self.assertFalse(self.user.groups.filter(name='customer').exists())

    def test_non_manager_cannot_change_user_group(self):
        url = reverse('accounts:change-group')
        data = {
            'username': self.manager.username,
            'new_group': 'customer'
        }
        response = self.user_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registration_requires_password(self):
        url = reverse('accounts:register')
        data = {
            'username': 'nopassworduser',
            'email': 'nopassword@g.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
