from django import forms
from django.utils import timezone
from .models import Olympiad, OlympiadTask, OlympiadTestCase, OlympiadTaskSubmission

import datetime


class OlympiadForm(forms.ModelForm):
    """Форма для создания и редактирования олимпиады"""
    
    class Meta:
        model = Olympiad
        fields = [
            'title', 
            'short_description', 
            'description', 
            'image', 
            'start_datetime', 
            'end_datetime', 
            'time_limit_minutes',
            'is_open',
            'min_passing_score',
            'is_rated',
            'related_course',
            'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'placeholder': 'Введите название олимпиады...'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'placeholder': 'Краткое описание (будет отображаться в списке олимпиад)...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white', 
                'rows': 8,
                'placeholder': 'Подробное описание олимпиады, правила, рекомендации...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm border border-gray-300 dark:border-gray-600 rounded-md shadow-sm cursor-pointer focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'accept': 'image/*',
                'id': 'olympiad-image'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'type': 'datetime-local'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'type': 'datetime-local'
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'min': '0',
                'placeholder': '0'
            }),
            'is_open': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:bg-gray-700 dark:border-gray-600'
            }),
            'min_passing_score': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white',
                'min': '0',
                'placeholder': '0'
            }),
            'is_rated': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:bg-gray-700 dark:border-gray-600'
            }),
            'related_course': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        # Проверяем, что дата окончания позже даты начала
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error('end_datetime', 'Дата окончания должна быть позже даты начала.')
        
        return cleaned_data


class ProblemForm(forms.ModelForm):
    """Форма для создания и редактирования задачи олимпиады"""
    
    class Meta:
        model = OlympiadTask
        fields = ['title', 'description', 'points', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 10}),
            'points': forms.NumberInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class TestCaseForm(forms.ModelForm):
    """Форма для создания и редактирования тестового случая"""
    
    class Meta:
        model = OlympiadTestCase
        fields = ['input_data', 'expected_output', 'is_hidden', 'explanation', 'points', 'order']
        widgets = {
            'input_data': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'expected_output': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'is_hidden': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'explanation': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class SubmissionForm(forms.ModelForm):
    """Форма для отправки решения задачи"""
    
    class Meta:
        model = OlympiadTaskSubmission
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