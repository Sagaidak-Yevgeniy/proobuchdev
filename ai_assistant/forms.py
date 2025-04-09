from django import forms
from .models import ChatSession, ChatMessage, AIFeedback


class MessageForm(forms.ModelForm):
    """Форма для отправки сообщения в чат"""
    
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Введите ваше сообщение...'
            })
        }
        labels = {
            'content': 'Сообщение'
        }


class FeedbackForm(forms.ModelForm):
    """Форма для отправки обратной связи о сообщении ассистента"""
    
    class Meta:
        model = AIFeedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-select'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Оставьте комментарий (необязательно)...'
            })
        }
        labels = {
            'rating': 'Оценка ответа',
            'comment': 'Комментарий'
        }