from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser, Profile
from .models import Course, Category, Enrollment

class CourseModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testteacher',
            email='teacher@example.com',
            password='testpassword'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role='teacher'
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            author=self.user,
            category=self.category,
            is_published=True
        )
        
    def test_course_creation(self):
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.author, self.user)
        self.assertEqual(self.course.category, self.category)
        self.assertTrue(self.course.is_published)
        self.assertTrue(self.course.slug)
        
    def test_course_slug_generation(self):
        self.assertEqual(self.course.slug, 'test-course')
        
    def test_course_string_representation(self):
        self.assertEqual(str(self.course), 'Test Course')
        
    def test_course_absolute_url(self):
        url = reverse('course_detail', kwargs={'slug': self.course.slug})
        self.assertEqual(self.course.get_absolute_url(), url)

class EnrollmentModelTests(TestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username='testteacher',
            email='teacher@example.com',
            password='testpassword'
        )
        Profile.objects.create(
            user=self.teacher,
            role='teacher'
        )
        
        self.student = CustomUser.objects.create_user(
            username='teststudent',
            email='student@example.com',
            password='testpassword'
        )
        Profile.objects.create(
            user=self.student,
            role='student'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            author=self.teacher,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course
        )
        
    def test_enrollment_creation(self):
        self.assertEqual(self.enrollment.user, self.student)
        self.assertEqual(self.enrollment.course, self.course)
        self.assertFalse(self.enrollment.is_completed)
        self.assertEqual(self.enrollment.progress, 0)
        
    def test_enrollment_string_representation(self):
        expected = f'{self.student.username} - {self.course.title}'
        self.assertEqual(str(self.enrollment), expected)
