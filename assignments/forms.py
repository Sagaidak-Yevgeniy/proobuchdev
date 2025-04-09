from django import forms
from .models import Assignment, AssignmentSubmission, TestCase

class AssignmentForm(forms.ModelForm):
    """Форма для создания и редактирования задания"""
    
    class Meta:
        model = Assignment
        fields = ['title', 'task_description', 'initial_code', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название задания'}),
            'task_description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Описание задания'}),
            'initial_code': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 10, 'placeholder': 'Начальный код (заготовка)'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'title': 'Название задания',
            'task_description': 'Описание задания',
            'initial_code': 'Начальный код',
            'is_public': 'Публичное задание'
        }

class TestCaseForm(forms.ModelForm):
    """Форма для создания и редактирования тестового случая"""
    
    class Meta:
        model = TestCase
        fields = ['input_data', 'expected_output', 'is_hidden']
        widgets = {
            'input_data': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Входные данные'}),
            'expected_output': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Ожидаемый результат'}),
            'is_hidden': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'input_data': 'Входные данные',
            'expected_output': 'Ожидаемый результат',
            'is_hidden': 'Скрытый тест'
        }

class SubmissionForm(forms.ModelForm):
    """Форма для отправки решения задания"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['code']
        widgets = {
            'code': forms.Textarea(attrs={'class': 'form-textarea code-editor', 'rows': 15, 'placeholder': 'Ваш код здесь...'})
        }
        labels = {
            'code': 'Ваш код'
        }
