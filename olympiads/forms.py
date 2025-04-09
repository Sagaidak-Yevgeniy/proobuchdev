from django import forms
from django.utils import timezone
from .models import Olympiad, Problem, TestCase, Submission

import datetime


class OlympiadForm(forms.ModelForm):
    """Форма для создания и редактирования олимпиады"""
    
    class Meta:
        model = Olympiad
        fields = ['title', 'description', 'start_time', 'end_time', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Проверяем, что дата окончания позже даты начала
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', 'Дата окончания должна быть позже даты начала.')
        
        return cleaned_data


class ProblemForm(forms.ModelForm):
    """Форма для создания и редактирования задачи олимпиады"""
    
    class Meta:
        model = Problem
        fields = ['title', 'description', 'time_limit', 'memory_limit', 'points', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 10}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-input'}),
            'memory_limit': forms.NumberInput(attrs={'class': 'form-input'}),
            'points': forms.NumberInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class TestCaseForm(forms.ModelForm):
    """Форма для создания и редактирования тестового случая"""
    
    class Meta:
        model = TestCase
        fields = ['input_data', 'expected_output', 'is_example', 'order']
        widgets = {
            'input_data': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'expected_output': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'is_example': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class SubmissionForm(forms.ModelForm):
    """Форма для отправки решения задачи"""
    
    class Meta:
        model = Submission
        fields = ['code']
        widgets = {
            'code': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 15}),
        }
        
    def clean_code(self):
        code = self.cleaned_data.get('code')
        
        # Проверка, что код не пустой
        if not code or code.strip() == '':
            raise forms.ValidationError('Код решения не может быть пустым.')
            
        # Проверка максимальной длины кода (например, 50 КБ)
        if len(code) > 50 * 1024:
            raise forms.ValidationError('Код слишком длинный. Максимальный размер 50 КБ.')
            
        return code