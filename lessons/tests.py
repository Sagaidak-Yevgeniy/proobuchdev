from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser, Profile
from courses.models import Course
from .models import Lesson, LessonContent, LessonCompletion

class LessonModelTests(TestCase):
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
        
        self.course = Course.objects.create(
            title='Test Course',
            description='This is a test course',
            author=self.teacher,
            is_published=True
        )
        
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title='Lesson 1',
            description='First lesson',
            order=1
        )
        
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title='Lesson 2',
            description='Second lesson',
            order=2
        )
        
        self.content = LessonContent.objects.create(
            lesson=self.lesson1,
            content_type='text',
            content='This is the content of lesson 1'
        )
    
    def test_lesson_creation(self):
        self.assertEqual(self.lesson1.title, 'Lesson 1')
        self.assertEqual(self.lesson1.course, self.course)
        self.assertEqual(self.lesson1.order, 1)
        
    def test_lesson_string_representation(self):
        expected = f'{self.course.title} - {self.lesson1.title}'
        self.assertEqual(str(self.lesson1), expected)
        
    def test_lesson_get_next_and_previous(self):
        self.assertEqual(self.lesson1.get_next_lesson(), self.lesson2)
        self.assertIsNone(self.lesson1.get_previous_lesson())
        
        self.assertIsNone(self.lesson2.get_next_lesson())
        self.assertEqual(self.lesson2.get_previous_lesson(), self.lesson1)
        
    def test_lesson_content_creation(self):
        self.assertEqual(self.content.lesson, self.lesson1)
        self.assertEqual(self.content.content_type, 'text')
        self.assertEqual(self.content.content, 'This is the content of lesson 1')
        
    def test_lesson_content_string_representation(self):
        expected = f'{self.lesson1.title} - Текст'
        self.assertEqual(str(self.content), expected)
        
    def test_lesson_content_is_assignment(self):
        self.assertFalse(self.content.is_assignment())
        
        assignment_content = LessonContent.objects.create(
            lesson=self.lesson2,
            content_type='assignment',
            content='Complete this assignment'
        )
        self.assertTrue(assignment_content.is_assignment())

class LessonCompletionTests(TestCase):
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
        
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Test Lesson',
            description='This is a test lesson',
            order=1
        )
        
        self.completion = LessonCompletion.objects.create(
            user=self.student,
            lesson=self.lesson,
            completed=False
        )
    
    def test_lesson_completion_creation(self):
        self.assertEqual(self.completion.user, self.student)
        self.assertEqual(self.completion.lesson, self.lesson)
        self.assertFalse(self.completion.completed)
        self.assertIsNone(self.completion.completed_at)
        
    def test_lesson_completion_string_representation(self):
        expected = f'{self.student.username} - {self.lesson.title} (не завершен)'
        self.assertEqual(str(self.completion), expected)
