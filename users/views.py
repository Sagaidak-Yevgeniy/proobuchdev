from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import CustomUserCreationForm, ProfileUpdateForm, UserUpdateForm, CustomAuthenticationForm, UserInterfaceForm
from .models import CustomUser, Profile, UserInterface
from educational_platform.csrf_hack import ensure_csrf_cookie as custom_ensure_csrf_cookie
from gamification.models import Achievement, UserAchievement, PointsHistory
from notifications.models import Notification
from django.urls import reverse


def grant_welcome_achievement(user):
    """
    Выдает приветственное достижение новому пользователю в зависимости от его роли
    
    Args:
        user (CustomUser): Пользователь, которому нужно выдать достижение
    """
    # Определяем тип достижения в зависимости от роли пользователя
    achievement_name = ""
    
    if user.profile.role == 'student':
        achievement_name = "Новый студент"
    elif user.profile.role == 'teacher':
        achievement_name = "Новый преподаватель"
    else:
        # Для других ролей не выдаем достижение
        return False
    
    try:
        # Проверяем, есть ли уже у пользователя какие-либо достижения "Новый студент" или "Новый преподаватель" 
        # и не выдаем дополнительных достижений, если они уже есть
        existing_achievement = UserAchievement.objects.filter(
            user=user, 
            achievement__name__in=["Новый студент", "Новый преподаватель"]
        ).first()
        
        if existing_achievement:
            print(f"DEBUG: Пользователь {user.username} уже имеет достижение {existing_achievement.achievement.name}")
            return False
            
        # Находим соответствующее достижение
        achievement = Achievement.objects.get(name=achievement_name)
        
        # Выдаем достижение
        user_achievement = UserAchievement.objects.create(
            user=user,
            achievement=achievement
        )
        
        # Добавляем историю начисления очков
        PointsHistory.objects.create(
            user=user,
            points=achievement.points,
            action='achievement',
            description=f"Получено достижение: {achievement.name}"
        )
        
        # Создаем уведомление о достижении
        achievement_notification = Notification.objects.create(
            user=user,
            title=f"Новое достижение: {achievement.name}",
            message=f"Вы получили достижение '{achievement.name}' и {achievement.points} очков!",
            notification_type='achievement',
            is_high_priority=True,
            url=reverse('achievement_list')
        )
        
        print(f"DEBUG: Выдано достижение {achievement_name} пользователю {user.username}")
        return True
    except Achievement.DoesNotExist:
        # Достижение не найдено, пропускаем
        print(f"DEBUG: Достижение {achievement_name} не найдено в системе")
        pass
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс регистрации
        print(f"ERROR: Ошибка при выдаче достижения: {str(e)}")
    
    return False

@ensure_csrf_cookie
def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            selected_role = form.cleaned_data.get('role')
            
            # Добавляем отладочную информацию
            print(f"DEBUG: User {username} созданный с ролью {selected_role}")
            print(f"DEBUG: Проверка профиля - роль в профиле: {user.profile.role}")
            
            # Выдаем достижение и отправляем приветственное уведомление
            try:
                achievement_granted = grant_welcome_achievement(user)
                if achievement_granted:
                    print(f"DEBUG: Welcome achievement granted to {username}")
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс регистрации
                print(f"ERROR: Failed to grant welcome achievement: {str(e)}")
            
            messages.success(request, f'Аккаунт {username} успешно создан! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    """Просмотр профиля текущего пользователя"""
    return render(request, 'users/profile.html')

@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    
    return render(request, 'users/profile_edit.html', context)

def user_profile(request, username):
    """Просмотр профиля другого пользователя"""
    user = get_object_or_404(CustomUser, username=username)
    return render(request, 'users/user_profile.html', {'user': user})

@login_required
def logout_view(request):
    """Выход пользователя из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home')
    
@ensure_csrf_cookie
@login_required
def interface_settings(request):
    """Настройка интерфейса пользователя"""
    if request.method == 'POST':
        form = UserInterfaceForm(request.POST, instance=request.user.interface)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки интерфейса успешно сохранены!')
            return redirect('profile')
    else:
        form = UserInterfaceForm(instance=request.user.interface)
    
    context = {
        'form': form,
        'title': 'Настройки интерфейса'
    }
    
    return render(request, 'users/interface_settings.html', context)

@ensure_csrf_cookie
def custom_login(request):
    """Кастомное представление для входа в систему"""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Проверяем, был ли это первый вход
                first_login = False
                if user.last_login is None or (user.date_joined and (user.last_login - user.date_joined).total_seconds() < 60):
                    first_login = True
                
                # Если это первый вход, проверяем наличие достижений и при необходимости выдаем
                if first_login:
                    try:
                        # Проверяем, есть ли у пользователя достижение Новый студент/преподаватель
                        achievement_name = "Новый студент" if user.profile.role == 'student' else "Новый преподаватель"
                        try:
                            achievement = Achievement.objects.get(name=achievement_name)
                            if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                                # Если достижения нет, выдаем его
                                grant_welcome_achievement(user)
                        except Achievement.DoesNotExist:
                            pass
                    except Exception as e:
                        # Логируем ошибку, но не прерываем процесс входа
                        print(f"ERROR: Failed to check/grant achievements on login: {str(e)}")
                
                messages.success(request, f'Вы успешно вошли как {username}.')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Ошибка аутентификации. Пожалуйста, проверьте имя пользователя и пароль.')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})
