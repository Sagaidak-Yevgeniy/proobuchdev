from django import forms
from .models import Lesson, LessonContent

class LessonForm(forms.ModelForm):
    """Форма для создания и редактирования урока"""
    
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название урока'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Краткое описание урока'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 1})
        }
        labels = {
            'title': 'Название урока',
            'description': 'Описание',
            'order': 'Порядковый номер'
        }

class LessonContentForm(forms.ModelForm):
    """Форма для создания и редактирования содержимого урока"""
    
    class Meta:
        model = LessonContent
        fields = ['content_type', 'content', 'video_url']
        widgets = {
            'content_type': forms.Select(attrs={'class': 'form-select', 'id': 'content-type-select'}),
            'content': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 10, 'placeholder': 'Содержимое урока', 'id': 'content-textarea'}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Ссылка на видео (YouTube)', 'id': 'video-url-input'})
        }
        labels = {
            'content_type': 'Тип содержимого',
            'content': 'Содержимое',
            'video_url': 'Ссылка на видео'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        content = cleaned_data.get('content')
        video_url = cleaned_data.get('video_url')
        
        if content_type == 'video' and not video_url:
            self.add_error('video_url', 'Для типа содержимого "Видео" необходимо указать ссылку на видео.')
        
        if content_type != 'video' and not content:
            self.add_error('content', f'Для типа содержимого "{content_type}" необходимо заполнить содержимое.')
        
        return cleaned_data
