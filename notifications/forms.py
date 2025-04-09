from django import forms
from .models import NotificationSettings, DeviceToken, NotificationChannel


class NotificationSettingsForm(forms.ModelForm):
    """Форма для редактирования настроек уведомлений"""
    
    class Meta:
        model = NotificationSettings
        fields = [
            'receive_all', 'notify_only_high_priority',
            'receive_achievement', 'receive_course', 'receive_lesson',
            'receive_assignment', 'receive_message', 'receive_system', 'receive_deadline',
            'email_notifications', 'email_digest',
            'push_notifications', 'quiet_hours_enabled',
            'quiet_hours_start', 'quiet_hours_end',
        ]
        widgets = {
            'receive_all': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notify_only_high_priority': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_achievement': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_course': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_lesson': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_assignment': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_message': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_system': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'receive_deadline': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'email_digest': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'push_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'quiet_hours_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'quiet_hours_start': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
        }


class DeviceTokenForm(forms.ModelForm):
    """Форма для регистрации токена устройства"""
    
    class Meta:
        model = DeviceToken
        fields = ['token', 'device_type', 'device_name']
        widgets = {
            'token': forms.TextInput(attrs={'class': 'form-input'}),
            'device_type': forms.Select(attrs={'class': 'form-select'}),
            'device_name': forms.TextInput(attrs={'class': 'form-input'}),
        }


class QuietHoursForm(forms.Form):
    """Форма для настройки тихих часов"""
    
    enabled = forms.BooleanField(
        required=False,
        label='Включить тихие часы',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    start_time = forms.TimeField(
        label='Начало тихих часов',
        widget=forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'})
    )
    end_time = forms.TimeField(
        label='Конец тихих часов',
        widget=forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'})
    )