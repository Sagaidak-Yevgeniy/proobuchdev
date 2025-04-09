from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Profile

class UserModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role='student'
        )
        
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword'))
        
    def test_profile_creation(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.role, 'student')
        
    def test_profile_role_methods(self):
        self.assertFalse(self.profile.is_teacher())
        self.assertFalse(self.profile.is_admin())
        
        # Изменение роли на преподавателя
        self.profile.role = 'teacher'
        self.profile.save()
        self.assertTrue(self.profile.is_teacher())
        self.assertFalse(self.profile.is_admin())
        
        # Изменение роли на администратора
        self.profile.role = 'admin'
        self.profile.save()
        self.assertTrue(self.profile.is_teacher())
        self.assertTrue(self.profile.is_admin())

class UserViewsTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role='student'
        )
        
    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        
        # Проверка аутентификации
        login_successful = self.client.login(username='testuser', password='testpassword')
        self.assertTrue(login_successful)
