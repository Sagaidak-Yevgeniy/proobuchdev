from django.test import TestCase
from django.urls import reverse
from users.models import CustomUser, Profile
from courses.models import Course
from lessons.models import Lesson, LessonContent
from .models import Assignment, TestCase as AssignmentTestCase, AssignmentSubmission
from .code_checker import run_code_with_test_case

class AssignmentModelTests(TestCase):
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
        
        self.lesson_content = LessonContent.objects.create(
            lesson=self.lesson,
            content_type='assignment',
            content='This is an assignment'
        )
        
        self.assignment = Assignment.objects.create(
            lesson_content=self.lesson_content,
            title='Test Assignment',
            task_description='Solve this problem',
            initial_code='def solution():\n    pass'
        )
        
        self.test_case = AssignmentTestCase.objects.create(
            assignment=self.assignment,
            input_data='5',
            expected_output='25'
        )
        
        self.submission = AssignmentSubmission.objects.create(
            user=self.student,
            assignment=self.assignment,
            code='def solution(n):\n    return n*n',
            status='pending'
        )
    
    def test_assignment_creation(self):
        self.assertEqual(self.assignment.title, 'Test Assignment')
        self.assertEqual(self.assignment.lesson_content, self.lesson_content)
        self.assertEqual(self.assignment.task_description, 'Solve this problem')
        self.assertEqual(self.assignment.initial_code, 'def solution():\n    pass')
        self.assertTrue(self.assignment.is_public)
        
    def test_test_case_creation(self):
        self.assertEqual(self.test_case.assignment, self.assignment)
        self.assertEqual(self.test_case.input_data, '5')
        self.assertEqual(self.test_case.expected_output, '25')
        self.assertFalse(self.test_case.is_hidden)
        
    def test_submission_creation(self):
        self.assertEqual(self.submission.user, self.student)
        self.assertEqual(self.submission.assignment, self.assignment)
        self.assertEqual(self.submission.code, 'def solution(n):\n    return n*n')
        self.assertEqual(self.submission.status, 'pending')
        self.assertEqual(self.submission.score, 0)

class CodeCheckerTests(TestCase):
    def test_run_code_with_test_case(self):
        code = """
def solution(n):
    return int(n) ** 2
"""
        test_input = "5"
        expected_output = "25"
        
        result, error = run_code_with_test_case(code, test_input, expected_output)
        self.assertTrue(result)
        self.assertIsNone(error)
        
        # Test with incorrect solution
        wrong_code = """
def solution(n):
    return int(n) + 2
"""
        result, error = run_code_with_test_case(wrong_code, test_input, expected_output)
        self.assertFalse(result)
        self.assertIsNotNone(error)
        
        # Test with syntax error
        syntax_error_code = """
def solution(n)
    return int(n) ** 2
"""
        result, error = run_code_with_test_case(syntax_error_code, test_input, expected_output)
        self.assertFalse(result)
        self.assertIsNotNone(error)
