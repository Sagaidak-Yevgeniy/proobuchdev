from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile, UserInterface

class CustomUserCreationForm(UserCreationForm):
    """Форма для регистрации нового пользователя"""
    
    # Переопределяем поле username для разрешения пробелов в ФИО
    username = forms.CharField(
        label='ФИО',
        max_length=150,
        help_text=_('Введите ваше полное имя, отчество и фамилию'),
        validators=[
            RegexValidator(
                regex=r'^[\w\s.@+-]+$',
                message=_('ФИО может содержать буквы, цифры, пробелы и символы @/./+/-/_'),
                code='invalid_username'
            ),
        ],
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите ФИО полностью'})
    )
    
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'})
    )
    
    # Убираем роль администратора из доступных опций при регистрации
    ROLE_CHOICES = [
        (Profile.STUDENT, 'Ученик'),
        (Profile.TEACHER, 'Преподаватель'),
    ]
    
    role = forms.ChoiceField(
        label='Роль',
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Подтверждение пароля'})
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # Извлекаем и устанавливаем имя и фамилию из ФИО (username)
        full_name = self.cleaned_data['username'].strip()
        name_parts = full_name.split(' ', 1)
        if len(name_parts) > 1:
            user.first_name = name_parts[0]
            user.last_name = name_parts[1]
        else:
            user.first_name = full_name
            user.last_name = ''
            
        selected_role = self.cleaned_data['role']
        print(f"DEBUG: Creating user with role: {selected_role}")
        
        if commit:
            user.save()
            
            # Создаем или обновляем профиль пользователя с выбранной ролью
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={'role': selected_role}
            )
            
            # Если профиль уже существовал, обновляем роль
            if not created:
                profile.role = selected_role
                profile.save()
            
            # Создаем настройки уведомлений для пользователя
            from notifications.models import NotificationSettings
            NotificationSettings.objects.get_or_create(user=user)
                
            print(f"DEBUG: Profile {'created' if created else 'updated'} with role: {profile.role}")
            
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """Форма для авторизации пользователя"""
    
    username = forms.CharField(
        label='ФИО или Email',
        validators=[
            RegexValidator(
                regex=r'^[\w\s.@+-]+$',
                message=_('ФИО может содержать буквы, цифры, пробелы и символы @/./+/-/_'),
                code='invalid_username'
            ),
        ],
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ФИО или Email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Пароль'})
    )

class ProfileUpdateForm(forms.ModelForm):
    """Форма для обновления профиля пользователя"""
    
    class Meta:
        model = Profile
        fields = ('bio', 'avatar')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'form-input'})
        }
        labels = {
            'bio': 'О себе',
            'avatar': 'Фотография профиля'
        }

class UserUpdateForm(forms.ModelForm):
    """Форма для обновления данных пользователя"""
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'})
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email'
        }


class UserInterfaceForm(forms.ModelForm):
    """Форма для настройки интерфейса пользователя"""
    
    class Meta:
        model = UserInterface
        fields = ('theme', 'font_size', 'layout', 'enable_animations', 'high_contrast')
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'font_size': forms.Select(attrs={'class': 'form-select'}),
            'layout': forms.Select(attrs={'class': 'form-select'}),
            'enable_animations': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'high_contrast': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'theme': 'Тема оформления',
            'font_size': 'Размер шрифта',
            'layout': 'Макет интерфейса',
            'enable_animations': 'Включить анимации',
            'high_contrast': 'Высокий контраст'
        }
