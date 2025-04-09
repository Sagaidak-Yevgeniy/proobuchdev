from django import forms
from .models import NotificationSettings


class NotificationSettingsForm(forms.ModelForm):
    """Форма для редактирования настроек уведомлений"""
    
    class Meta:
        model = NotificationSettings
        fields = [
            'receive_all', 'notify_only_high_priority',
            'receive_achievement', 'receive_course', 'receive_lesson',
            'receive_assignment', 'receive_message',
            'email_notifications', 'email_digest'
        ]
        widgets = {
            'receive_all': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notify_only_high_priority': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_achievement': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_course': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_lesson': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_assignment': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_message': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'email_digest': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }