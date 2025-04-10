from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
import json
from datetime import datetime

from .models_goals import StudentGoal, GoalStep


@login_required
def get_student_goals(request):
    """API-эндпоинт для получения целей студента"""
    user = request.user
    
    # Получаем параметры из запроса
    status = request.GET.get('status', 'all')  # all, active, completed
    priority = request.GET.get('priority', None)  # low, medium, high
    course_id = request.GET.get('course_id', None)
    
    # Базовый запрос
    goals_query = StudentGoal.objects.filter(user=user)
    
    # Фильтрация по статусу
    if status == 'active':
        goals_query = goals_query.filter(is_completed=False)
    elif status == 'completed':
        goals_query = goals_query.filter(is_completed=True)
    
    # Фильтрация по приоритету
    if priority:
        goals_query = goals_query.filter(priority=priority)
    
    # Фильтрация по курсу
    if course_id:
        goals_query = goals_query.filter(course_id=course_id)
    
    # Сортируем: сначала по приоритету (высокий, средний, низкий), 
    # затем незавершенные перед завершенными, 
    # затем по дате создания (сначала новые)
    goals_query = goals_query.order_by(
        '-priority',  # Сначала высокий приоритет
        'is_completed',  # Сначала незавершенные
        '-created_at'  # Сначала новые
    )
    
    # Готовим данные для ответа
    goals_data = []
    for goal in goals_query:
        # Получаем все шаги цели
        steps = []
        for step in goal.steps.all().order_by('order'):
            steps.append({
                'id': step.id,
                'title': step.title,
                'description': step.description,
                'order': step.order,
                'is_completed': step.is_completed,
                'completed_at': step.completed_at.strftime('%Y-%m-%d %H:%M:%S') if step.completed_at else None
            })
        
        goals_data.append({
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'goal_type': goal.goal_type,
            'goal_type_display': goal.get_goal_type_display(),
            'priority': goal.priority,
            'priority_display': goal.get_priority_display(),
            'created_at': goal.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': goal.due_date.strftime('%Y-%m-%d') if goal.due_date else None,
            'is_completed': goal.is_completed,
            'completed_at': goal.completed_at.strftime('%Y-%m-%d %H:%M:%S') if goal.completed_at else None,
            'progress': goal.progress,
            'is_overdue': goal.is_overdue,
            'days_left': goal.days_left,
            'course': {
                'id': goal.course.id,
                'title': goal.course.title,
                'slug': goal.course.slug
            } if goal.course else None,
            'steps': steps
        })
    
    return JsonResponse({
        'goals': goals_data,
        'total': len(goals_data),
        'active': len([g for g in goals_data if not g['is_completed']]),
        'completed': len([g for g in goals_data if g['is_completed']]),
        'overdue': len([g for g in goals_data if g['is_overdue']])
    })


@login_required
def get_goal_details(request, goal_id):
    """API-эндпоинт для получения детальной информации о цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        
        # Получаем все шаги цели
        steps = []
        for step in goal.steps.all().order_by('order'):
            steps.append({
                'id': step.id,
                'title': step.title,
                'description': step.description,
                'order': step.order,
                'is_completed': step.is_completed,
                'completed_at': step.completed_at.strftime('%Y-%m-%d %H:%M:%S') if step.completed_at else None
            })
        
        goal_data = {
            'id': goal.id,
            'title': goal.title,
            'description': goal.description,
            'goal_type': goal.goal_type,
            'goal_type_display': goal.get_goal_type_display(),
            'priority': goal.priority,
            'priority_display': goal.get_priority_display(),
            'created_at': goal.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': goal.due_date.strftime('%Y-%m-%d') if goal.due_date else None,
            'is_completed': goal.is_completed,
            'completed_at': goal.completed_at.strftime('%Y-%m-%d %H:%M:%S') if goal.completed_at else None,
            'progress': goal.progress,
            'is_overdue': goal.is_overdue,
            'days_left': goal.days_left,
            'course': {
                'id': goal.course.id,
                'title': goal.course.title,
                'slug': goal.course.slug
            } if goal.course else None,
            'steps': steps
        }
        
        return JsonResponse({
            'success': True,
            'goal': goal_data
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def create_goal(request):
    """API-эндпоинт для создания новой цели"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        # Проверяем обязательные поля
        if 'title' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Поле title обязательно'
            }, status=400)
        
        # Создаем новую цель
        goal = StudentGoal(
            title=data['title'],
            description=data.get('description', ''),
            user=user,
            goal_type=data.get('goal_type', 'custom'),
            priority=data.get('priority', 'medium')
        )
        
        # Если указана дата выполнения
        due_date = data.get('due_date')
        if due_date:
            try:
                goal.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Некорректный формат даты. Используйте YYYY-MM-DD'
                }, status=400)
        
        # Если указан курс, связываем с ним
        course_id = data.get('course_id')
        if course_id:
            from courses.models import Course
            try:
                course = Course.objects.get(id=course_id)
                goal.course = course
            except Course.DoesNotExist:
                pass
        
        goal.save()
        
        # Если указаны шаги, создаем их
        steps_data = data.get('steps', [])
        for i, step_data in enumerate(steps_data):
            if 'title' in step_data:
                GoalStep.objects.create(
                    goal=goal,
                    title=step_data['title'],
                    description=step_data.get('description', ''),
                    order=i + 1
                )
        
        return JsonResponse({
            'success': True,
            'goal_id': goal.id,
            'message': 'Цель успешно создана'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_goal(request, goal_id):
    """API-эндпоинт для обновления цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        data = json.loads(request.body)
        
        # Обновляем поля цели
        if 'title' in data:
            goal.title = data['title']
        if 'description' in data:
            goal.description = data['description']
        if 'goal_type' in data:
            goal.goal_type = data['goal_type']
        if 'priority' in data:
            goal.priority = data['priority']
        
        # Если указана дата выполнения
        if 'due_date' in data:
            due_date = data['due_date']
            if due_date:
                try:
                    goal.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Некорректный формат даты. Используйте YYYY-MM-DD'
                    }, status=400)
            else:
                goal.due_date = None
        
        # Если указан статус выполнения
        if 'is_completed' in data:
            goal.is_completed = data['is_completed']
        
        # Если указан курс, связываем с ним
        if 'course_id' in data:
            course_id = data['course_id']
            if course_id:
                from courses.models import Course
                try:
                    course = Course.objects.get(id=course_id)
                    goal.course = course
                except Course.DoesNotExist:
                    goal.course = None
            else:
                goal.course = None
        
        goal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Цель успешно обновлена'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_goal(request, goal_id):
    """API-эндпоинт для удаления цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        goal.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Цель успешно удалена'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def create_goal_step(request, goal_id):
    """API-эндпоинт для создания нового шага цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        data = json.loads(request.body)
        
        # Проверяем обязательные поля
        if 'title' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Поле title обязательно'
            }, status=400)
        
        # Определяем порядковый номер нового шага
        order = GoalStep.objects.filter(goal=goal).count() + 1
        
        # Создаем новый шаг
        step = GoalStep.objects.create(
            goal=goal,
            title=data['title'],
            description=data.get('description', ''),
            order=order
        )
        
        return JsonResponse({
            'success': True,
            'step_id': step.id,
            'message': 'Шаг успешно создан'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def update_goal_step(request, goal_id, step_id):
    """API-эндпоинт для обновления шага цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        step = GoalStep.objects.get(id=step_id, goal=goal)
        
        data = json.loads(request.body)
        
        # Обновляем поля шага
        if 'title' in data:
            step.title = data['title']
        if 'description' in data:
            step.description = data['description']
        if 'order' in data:
            step.order = data['order']
        if 'is_completed' in data:
            step.is_completed = data['is_completed']
        
        step.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Шаг успешно обновлен'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except GoalStep.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Шаг не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_goal_step(request, goal_id, step_id):
    """API-эндпоинт для удаления шага цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        step = GoalStep.objects.get(id=step_id, goal=goal)
        
        step.delete()
        
        # Переупорядочиваем оставшиеся шаги
        for i, s in enumerate(goal.steps.all().order_by('order')):
            s.order = i + 1
            s.save(update_fields=['order'])
        
        # Обновляем прогресс цели
        if goal.steps.count() > 0:
            completed_steps = goal.steps.filter(is_completed=True).count()
            goal.progress = int((completed_steps / goal.steps.count()) * 100)
            goal.save(update_fields=['progress'])
        
        return JsonResponse({
            'success': True,
            'message': 'Шаг успешно удален'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except GoalStep.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Шаг не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def toggle_goal_step(request, goal_id, step_id):
    """API-эндпоинт для переключения статуса шага цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        step = GoalStep.objects.get(id=step_id, goal=goal)
        
        # Переключаем статус шага
        step.is_completed = not step.is_completed
        step.save()
        
        return JsonResponse({
            'success': True,
            'is_completed': step.is_completed,
            'message': f'Шаг отмечен как {"выполненный" if step.is_completed else "невыполненный"}'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except GoalStep.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Шаг не найден'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def toggle_goal(request, goal_id):
    """API-эндпоинт для переключения статуса цели"""
    user = request.user
    
    try:
        goal = StudentGoal.objects.get(id=goal_id, user=user)
        
        # Переключаем статус цели
        goal.is_completed = not goal.is_completed
        goal.save()
        
        return JsonResponse({
            'success': True,
            'is_completed': goal.is_completed,
            'message': f'Цель отмечена как {"выполненная" if goal.is_completed else "невыполненная"}'
        })
        
    except StudentGoal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Цель не найдена'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)