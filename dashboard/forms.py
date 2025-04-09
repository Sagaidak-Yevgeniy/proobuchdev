from django import forms

from .models import Widget, DashboardLayout


class WidgetForm(forms.ModelForm):
    """Форма для создания и редактирования виджетов"""
    
    class Meta:
        model = Widget
        fields = ['title', 'widget_type', 'size', 'is_active', 'settings']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Название виджета'}),
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'settings': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'placeholder': 'Настройки в формате JSON'})
        }


class DashboardLayoutForm(forms.ModelForm):
    """Форма для настройки макета дашборда"""
    
    class Meta:
        model = DashboardLayout
        fields = ['theme', 'animation_speed']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'animation_speed': forms.Select(attrs={'class': 'form-select'}),
        }


class WidgetPositionForm(forms.Form):
    """Форма для изменения позиции виджета"""
    
    widget_id = forms.IntegerField(widget=forms.HiddenInput())
    position_x = forms.IntegerField(min_value=0)
    position_y = forms.IntegerField(min_value=0)


class WidgetSizeForm(forms.Form):
    """Форма для изменения размера виджета"""
    
    widget_id = forms.IntegerField(widget=forms.HiddenInput())
    size = forms.ChoiceField(choices=Widget.SIZE_CHOICES)