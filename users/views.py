from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import CustomUserCreationForm, ProfileUpdateForm, UserUpdateForm, CustomAuthenticationForm
from .models import CustomUser, Profile
from educational_platform.csrf_hack import ensure_csrf_cookie as custom_ensure_csrf_cookie

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
