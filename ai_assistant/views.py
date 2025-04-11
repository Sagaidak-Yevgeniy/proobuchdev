from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import ChatSession, ChatMessage, CodeSnippet, AIFeedback
from .ai_service import ai_assistant
from courses.models import Course
from lessons.models import Lesson
from assignments.models import Assignment

import json
import re


@login_required
def chat_history(request):
    """Отображает историю чатов пользователя"""
    sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    return render(request, 'ai_assistant/chat_history.html', {
        'sessions': sessions,
    })


@login_required
@require_POST
def chat_delete(request, session_id):
    """Удаляет чат с AI-ассистентом"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    messages.success(request, "Чат успешно удален")
    return redirect('chat_history')


@login_required
def chat_detail(request, session_id):
    """Отображает детали чата"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.all().order_by('created_at')
    
    # Проверяем доступность API
    ai_available = ai_assistant.is_available()
    
    return render(request, 'ai_assistant/chat_detail.html', {
        'session': session,
        'messages': messages,
        'ai_available': ai_available,
    })


@login_required
def chat_new(request):
    """Создает новый чат без контекста"""
    title = f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
    session = ChatSession.objects.create(
        user=request.user,
        title=title,
    )
    
    # Добавляем системное сообщение
    ChatMessage.objects.create(
        session=session,
        role='system',
        content="Чат начат. Задайте вопрос AI-ассистенту."
    )
    
    return redirect('chat_detail', session_id=session.id)


@login_required
def chat_new_with_context(request, context_type, context_id):
    """Создает новый чат с контекстом курса, урока или задания"""
    context_object = None
    title = f"Новый чат {timezone.now().strftime('%d.%m.%Y %H:%M')}"
    session_kwargs = {'user': request.user, 'title': title}
    
    if context_type == 'course':
        context_object = get_object_or_404(Course, id=context_id)
        session_kwargs['course'] = context_object
        title = f"Чат по курсу: {context_object.title}"
    elif context_type == 'lesson':
        context_object = get_object_or_404(Lesson, id=context_id)
        session_kwargs['lesson'] = context_object
        session_kwargs['course'] = context_object.module.course
        title = f"Чат по уроку: {context_object.title}"
    elif context_type == 'assignment':
        context_object = get_object_or_404(Assignment, id=context_id)
        session_kwargs['assignment'] = context_object
        lesson_content = context_object.lesson_content
        session_kwargs['lesson'] = lesson_content.lesson
        session_kwargs['course'] = lesson_content.lesson.module.course
        title = f"Чат по заданию: {context_object.title}"
    else:
        messages.error(request, "Неверный тип контекста")
        return redirect('chat_history')
    
    session_kwargs['title'] = title
    session = ChatSession.objects.create(**session_kwargs)
    
    # Добавляем системное сообщение
    ChatMessage.objects.create(
        session=session,
        role='system',
        content=f"Чат начат с контекстом: {title}"
    )
    
    return redirect('chat_detail', session_id=session.id)


@login_required
@require_POST
def chat_send_message(request, session_id):
    """Отправляет сообщение в чат и получает ответ от AI"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    # Получаем текст сообщения
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
    except json.JSONDecodeError:
        message_text = request.POST.get('message', '').strip()
    
    if not message_text:
        return JsonResponse({
            'success': False,
            'error': 'Сообщение не может быть пустым'
        })
    
    # Создаем сообщение пользователя
    user_message = ChatMessage.objects.create(
        session=session,
        role='user',
        content=message_text
    )
    
    # Обновляем время последнего сообщения в сессии
    session.updated_at = timezone.now()
    
    # Проверяем, если это первое сообщение пользователя, обновляем название чата
    user_messages = session.messages.filter(role='user').count()
    if user_messages == 1:
        # Ограничиваем длину вопроса для названия
        short_question = message_text[:50] + ('...' if len(message_text) > 50 else '')
        current_time = timezone.now().strftime('%d.%m.%Y %H:%M')
        # Обновляем название чата с первым вопросом и временем
        session.title = f"{short_question} ({current_time})"
    
    session.save()
    
    # Извлекаем сниппеты кода из сообщения
    code_pattern = r'```(\w*)\n([\s\S]*?)\n```'
    code_matches = re.findall(code_pattern, message_text)
    
    for language, code in code_matches:
        language = language.lower() if language else 'other'
        if language not in [choice[0] for choice in CodeSnippet.LANGUAGE_CHOICES]:
            language = 'other'
        
        CodeSnippet.objects.create(
            message=user_message,
            code=code,
            language=language
        )
    
    # Проверяем доступность API
    if not ai_assistant.is_available():
        # Если API недоступен, отправляем сообщение об ошибке
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content="Извините, AI-ассистент временно недоступен. Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        
        return JsonResponse({
            'success': False,
            'error': 'AI-ассистент недоступен',
            'message_id': user_message.id
        })
    
    # Получаем контекст сессии
    context = session.get_context_dict()
    
    # Получаем ответ от AI
    ai_response = ai_assistant.generate_response(message_text, context)
    
    if ai_response['success']:
        # Создаем сообщение ассистента
        assistant_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response['message']
        )
        
        # Извлекаем сниппеты кода из ответа ассистента
        code_matches = re.findall(code_pattern, ai_response['message'])
        
        for language, code in code_matches:
            language = language.lower() if language else 'other'
            if language not in [choice[0] for choice in CodeSnippet.LANGUAGE_CHOICES]:
                language = 'other'
            
            CodeSnippet.objects.create(
                message=assistant_message,
                code=code,
                language=language
            )
        
        return JsonResponse({
            'success': True,
            'message': ai_response['message'],
            'message_id': assistant_message.id
        })
    else:
        # Если произошла ошибка, отправляем сообщение об ошибке
        error_message = ChatMessage.objects.create(
            session=session,
            role='system',
            content=f"Ошибка: {ai_response['message']}"
        )
        
        return JsonResponse({
            'success': False,
            'error': ai_response['message'],
            'message_id': error_message.id
        })


@login_required
@require_POST
def chat_feedback(request, session_id, message_id):
    """Сохраняет обратную связь о сообщении ассистента"""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    message = get_object_or_404(ChatMessage, id=message_id, session=session, role='assistant')
    
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        comment = data.get('comment', '')
    except (json.JSONDecodeError, ValueError):
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
    
    if rating < 1 or rating > 5:
        return JsonResponse({
            'success': False,
            'error': 'Оценка должна быть от 1 до 5'
        })
    
    # Создаем или обновляем обратную связь
    feedback, created = AIFeedback.objects.update_or_create(
        message=message,
        user=request.user,
        defaults={
            'rating': rating,
            'comment': comment
        }
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Спасибо за обратную связь!'
    })