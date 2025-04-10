from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
import json
from datetime import datetime, timedelta

from .models_events import Event, EventParticipant
from notifications.models import Notification


@login_required
def get_events(request):
    """API-эндпоинт для получения списка мероприятий"""
    user = request.user
    now = timezone.now()
    
    # Получаем параметры из запроса
    period = request.GET.get('period', 'upcoming')  # upcoming, past, all
    event_type = request.GET.get('type', None)
    course_id = request.GET.get('course_id', None)
    
    # Базовый запрос
    events_query = Event.objects.filter(
        is_public=True
    ).order_by('start_time')
    
    # Дополнительно фильтруем мероприятия, созданные текущим пользователем
    user_events = Event.objects.filter(
        created_by=user
    ).order_by('start_time')
    
    # Фильтрация по периоду
    if period == 'upcoming':
        events_query = events_query.filter(end_time__gte=now)
        user_events = user_events.filter(end_time__gte=now)
    elif period == 'past':
        events_query = events_query.filter(end_time__lt=now)
        user_events = user_events.filter(end_time__lt=now)
    
    # Фильтрация по типу мероприятия
    if event_type:
        events_query = events_query.filter(event_type=event_type)
        user_events = user_events.filter(event_type=event_type)
    
    # Фильтрация по курсу
    if course_id:
        events_query = events_query.filter(course_id=course_id)
        user_events = user_events.filter(course_id=course_id)
    
    # Объединяем запросы (без дубликатов)
    all_events = list(events_query) + [e for e in user_events if e not in events_query]
    
    # Готовим данные для ответа
    events_data = []
    for event in all_events:
        # Проверяем, зарегистрирован ли пользователь на мероприятие
        is_registered = EventParticipant.objects.filter(
            event=event, 
            user=user
        ).exists()
        
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'start_time': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'location': event.location,
            'url': event.url,
            'created_by': {
                'id': event.created_by.id,
                'username': event.created_by.username,
                'full_name': f"{event.created_by.first_name} {event.created_by.last_name}".strip() or event.created_by.username
            },
            'is_public': event.is_public,
            'max_participants': event.max_participants,
            'participants_count': event.participants_count,
            'is_full': event.is_full,
            'is_past': event.is_past,
            'is_ongoing': event.is_ongoing,
            'is_upcoming': event.is_upcoming,
            'is_registered': is_registered,
            'is_owner': event.created_by.id == user.id,
            'course': {
                'id': event.course.id,
                'title': event.course.title,
                'slug': event.course.slug
            } if event.course else None
        })
    
    return JsonResponse({
        'events': events_data,
        'total': len(events_data)
    })


@login_required
def get_event_details(request, event_id):
    """API-эндпоинт для получения детальной информации о мероприятии"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, может ли пользователь просматривать детали мероприятия
        if not event.is_public and event.created_by != user:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет доступа к этому мероприятию'
            }, status=403)
        
        # Проверяем, зарегистрирован ли пользователь на мероприятие
        participant = EventParticipant.objects.filter(
            event=event, 
            user=user
        ).first()
        
        # Получаем список участников
        participants = []
        if event.created_by == user or participant:
            for p in event.participants.all():
                participants.append({
                    'id': p.user.id,
                    'username': p.user.username,
                    'full_name': f"{p.user.first_name} {p.user.last_name}".strip() or p.user.username,
                    'status': p.status,
                    'status_display': p.get_status_display(),
                    'registered_at': p.registered_at.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'start_time': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'location': event.location,
            'url': event.url,
            'created_by': {
                'id': event.created_by.id,
                'username': event.created_by.username,
                'full_name': f"{event.created_by.first_name} {event.created_by.last_name}".strip() or event.created_by.username
            },
            'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_public': event.is_public,
            'max_participants': event.max_participants,
            'participants_count': event.participants_count,
            'is_full': event.is_full,
            'is_past': event.is_past,
            'is_ongoing': event.is_ongoing,
            'is_upcoming': event.is_upcoming,
            'is_registered': participant is not None,
            'registration_status': participant.status if participant else None,
            'registration_status_display': participant.get_status_display() if participant else None,
            'is_owner': event.created_by.id == user.id,
            'course': {
                'id': event.course.id,
                'title': event.course.title,
                'slug': event.course.slug
            } if event.course else None,
            'participants': participants
        }
        
        return JsonResponse({
            'success': True,
            'event': event_data
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def create_event(request):
    """API-эндпоинт для создания нового мероприятия"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        # Проверяем обязательные поля
        required_fields = ['title', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Поле {field} обязательно'
                }, status=400)
        
        # Создаем новое мероприятие
        event = Event(
            title=data['title'],
            description=data.get('description', ''),
            event_type=data.get('event_type', 'other'),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            location=data.get('location', ''),
            url=data.get('url', ''),
            created_by=user,
            is_public=data.get('is_public', True),
            max_participants=data.get('max_participants', 0)
        )
        
        # Если указан курс, связываем с ним
        course_id = data.get('course_id')
        if course_id:
            from courses.models import Course
            try:
                course = Course.objects.get(id=course_id)
                event.course = course
            except Course.DoesNotExist:
                pass
        
        event.save()
        
        # Создаем уведомления для участников курса, если событие связано с курсом
        if event.course and event.is_public:
            from courses.models import Enrollment
            enrollments = Enrollment.objects.filter(course=event.course)
            
            for enrollment in enrollments:
                if enrollment.user != user:  # Не отправляем уведомление создателю события
                    Notification.objects.create(
                        user=enrollment.user,
                        notification_type='event_created',
                        message=f'Создано новое мероприятие "{event.title}" для курса "{event.course.title}"',
                        object_id=event.id,
                        content_type='event'
                    )
        
        return JsonResponse({
            'success': True,
            'event_id': event.id,
            'message': 'Мероприятие успешно создано'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_event(request, event_id):
    """API-эндпоинт для обновления мероприятия"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, имеет ли пользователь право редактировать мероприятие
        if event.created_by != user:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на редактирование этого мероприятия'
            }, status=403)
        
        data = json.loads(request.body)
        
        # Обновляем поля мероприятия
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'start_time' in data:
            event.start_time = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data:
            event.end_time = datetime.fromisoformat(data['end_time'])
        if 'location' in data:
            event.location = data['location']
        if 'url' in data:
            event.url = data['url']
        if 'is_public' in data:
            event.is_public = data['is_public']
        if 'max_participants' in data:
            event.max_participants = data['max_participants']
        
        # Если указан курс, связываем с ним
        if 'course_id' in data:
            from courses.models import Course
            try:
                course = Course.objects.get(id=data['course_id'])
                event.course = course
            except Course.DoesNotExist:
                event.course = None
        
        event.save()
        
        # Уведомляем участников о изменении мероприятия
        for participant in event.participants.all():
            if participant.user != user:  # Не отправляем уведомление создателю события
                Notification.objects.create(
                    user=participant.user,
                    notification_type='event_updated',
                    message=f'Мероприятие "{event.title}" было обновлено',
                    object_id=event.id,
                    content_type='event'
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Мероприятие успешно обновлено'
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_event(request, event_id):
    """API-эндпоинт для удаления мероприятия"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, имеет ли пользователь право удалять мероприятие
        if event.created_by != user:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на удаление этого мероприятия'
            }, status=403)
        
        # Уведомляем участников о отмене мероприятия
        for participant in event.participants.all():
            Notification.objects.create(
                user=participant.user,
                notification_type='event_cancelled',
                message=f'Мероприятие "{event.title}" было отменено',
                object_id=None,
                content_type='event'
            )
        
        # Удаляем мероприятие
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Мероприятие успешно удалено'
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def register_for_event(request, event_id):
    """API-эндпоинт для регистрации на мероприятие"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, можно ли зарегистрироваться на мероприятие
        if event.is_past:
            return JsonResponse({
                'success': False,
                'error': 'Мероприятие уже прошло'
            }, status=400)
        
        if event.is_full:
            return JsonResponse({
                'success': False,
                'error': 'Мероприятие уже заполнено'
            }, status=400)
        
        # Проверяем, не зарегистрирован ли пользователь уже
        participant, created = EventParticipant.objects.get_or_create(
            event=event,
            user=user,
            defaults={'status': 'registered'}
        )
        
        if not created:
            return JsonResponse({
                'success': False,
                'error': 'Вы уже зарегистрированы на это мероприятие'
            }, status=400)
        
        # Уведомляем организатора о новом участнике
        Notification.objects.create(
            user=event.created_by,
            notification_type='event_registration',
            message=f'Пользователь {user.username} зарегистрировался на мероприятие "{event.title}"',
            object_id=event.id,
            content_type='event'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Вы успешно зарегистрировались на мероприятие'
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def cancel_registration(request, event_id):
    """API-эндпоинт для отмены регистрации на мероприятие"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, зарегистрирован ли пользователь
        try:
            participant = EventParticipant.objects.get(
                event=event,
                user=user
            )
            
            # Удаляем участника
            participant.delete()
            
            # Уведомляем организатора об отмене регистрации
            Notification.objects.create(
                user=event.created_by,
                notification_type='event_registration_cancelled',
                message=f'Пользователь {user.username} отменил регистрацию на мероприятие "{event.title}"',
                object_id=event.id,
                content_type='event'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Регистрация на мероприятие отменена'
            })
            
        except EventParticipant.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Вы не зарегистрированы на это мероприятие'
            }, status=400)
            
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_participant_status(request, event_id, user_id):
    """API-эндпоинт для обновления статуса участника мероприятия"""
    current_user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, имеет ли пользователь право обновлять статус участников
        if event.created_by != current_user:
            return JsonResponse({
                'success': False,
                'error': 'У вас нет прав на обновление статуса участников'
            }, status=403)
        
        data = json.loads(request.body)
        status = data.get('status')
        
        if not status or status not in [s[0] for s in EventParticipant.STATUS_CHOICES]:
            return JsonResponse({
                'success': False,
                'error': 'Указан некорректный статус'
            }, status=400)
        
        # Обновляем статус участника
        participant = EventParticipant.objects.get(
            event=event,
            user_id=user_id
        )
        
        participant.status = status
        
        # Если статус "присутствовал", установим время присутствия
        if status == 'attended' and not participant.attended_at:
            participant.attended_at = timezone.now()
        
        participant.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Статус участника обновлен'
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except EventParticipant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Участник не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def send_event_feedback(request, event_id):
    """API-эндпоинт для отправки обратной связи о мероприятии"""
    user = request.user
    
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверяем, зарегистрирован ли пользователь и прошло ли мероприятие
        try:
            participant = EventParticipant.objects.get(
                event=event,
                user=user
            )
            
            if not event.is_past:
                return JsonResponse({
                    'success': False,
                    'error': 'Мероприятие еще не завершилось'
                }, status=400)
            
            data = json.loads(request.body)
            feedback = data.get('feedback', '')
            rating = data.get('rating')
            
            # Обновляем данные обратной связи
            participant.feedback = feedback
            
            if rating is not None:
                try:
                    rating = int(rating)
                    if 1 <= rating <= 5:
                        participant.rating = rating
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': 'Оценка должна быть от 1 до 5'
                        }, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': 'Некорректное значение оценки'
                    }, status=400)
            
            participant.save()
            
            # Уведомляем организатора о новой обратной связи
            Notification.objects.create(
                user=event.created_by,
                notification_type='event_feedback',
                message=f'Пользователь {user.username} оставил отзыв о мероприятии "{event.title}"',
                object_id=event.id,
                content_type='event'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Обратная связь успешно отправлена'
            })
            
        except EventParticipant.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Вы не являетесь участником этого мероприятия'
            }, status=400)
            
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Мероприятие не найдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)