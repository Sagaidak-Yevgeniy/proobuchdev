from django import forms
from .models import Course, Category

class CourseForm(forms.ModelForm):
    """Форма для создания и редактирования курса"""
    
    class Meta:
        model = Course
        fields = ['title', 'category', 'description', 'cover_image', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название курса'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Описание курса'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'title': 'Название курса',
            'category': 'Категория',
            'description': 'Описание',
            'cover_image': 'Обложка курса',
            'is_published': 'Опубликовать курс'
        }
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Название курса должно содержать не менее 5 символов')
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError('Описание курса должно содержать не менее 20 символов')
        return description

class CategoryForm(forms.ModelForm):
    """Форма для создания и редактирования категории"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название категории'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Описание категории'})
        }
        labels = {
            'name': 'Название категории',
            'description': 'Описание'
        }
