from django import forms
from .models import NotificationSettings


class NotificationSettingsForm(forms.ModelForm):
    """Форма настроек уведомлений пользователя"""
    
    class Meta:
        model = NotificationSettings
        fields = [
            'receive_all',
            'notify_only_high_priority',
            'receive_achievement',
            'receive_course',
            'receive_lesson',
            'receive_assignment',
            'receive_message',
            'email_notifications',
            'email_digest',
        ]
        widgets = {
            'receive_all': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'notify_only_high_priority': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'receive_achievement': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'receive_course': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'receive_lesson': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'receive_assignment': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'receive_message': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
            'email_digest': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-blue-600'}),
        }
        labels = {
            'receive_all': 'Получать все уведомления',
            'notify_only_high_priority': 'Получать только важные уведомления',
            'receive_achievement': 'Уведомления о достижениях',
            'receive_course': 'Уведомления о курсах',
            'receive_lesson': 'Уведомления об уроках',
            'receive_assignment': 'Уведомления о заданиях',
            'receive_message': 'Уведомления о сообщениях',
            'email_notifications': 'Email-уведомления',
            'email_digest': 'Еженедельная сводка на email',
        }
        help_texts = {
            'receive_all': 'Если отключено, вы не будете получать никаких уведомлений',
            'notify_only_high_priority': 'Получать уведомления только с высоким приоритетом',
            'receive_achievement': 'Получать уведомления о новых достижениях и наградах',
            'receive_course': 'Получать уведомления об обновлениях в курсах',
            'receive_lesson': 'Получать уведомления о новых уроках',
            'receive_assignment': 'Получать уведомления о заданиях и их проверке',
            'receive_message': 'Получать уведомления о новых сообщениях',
            'email_notifications': 'Дублировать уведомления на email',
            'email_digest': 'Получать еженедельную сводку активности на email',
        }