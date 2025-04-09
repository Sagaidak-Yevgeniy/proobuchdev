from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, UserInterface
from notifications.models import Notification

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """Создает профиль пользователя при создании нового пользователя"""
    # Если профиль уже создан в форме регистрации, не будем его пересоздавать
    if created:
        # Проверяем, существует ли уже профиль для этого пользователя
        if not Profile.objects.filter(user=instance).exists():
            # Только если профиль ещё не создан, создаем его с ролью студента по умолчанию
            print(f"DEBUG Signal: Creating default profile for user {instance.username}")
            Profile.objects.create(user=instance, role=Profile.STUDENT)
        else:
            print(f"DEBUG Signal: Profile already exists for user {instance.username}, not creating default")

@receiver(post_save, sender=CustomUser)
def save_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при обновлении пользователя"""
    # Проверяем, существует ли профиль, чтобы не перезаписывать его
    if hasattr(instance, 'profile'):
        # Если у нас уже есть связь с профилем, просто сохраняем его
        # Но не вызываем save() чтобы не срабатывал сигнал post_save для профиля
        print(f"DEBUG Signal: Profile relation exists for user {instance.username}")
    else:
        try:
            # Пробуем найти профиль в базе данных
            profile = Profile.objects.get(user=instance)
            print(f"DEBUG Signal: Found profile for user {instance.username}")
        except Profile.DoesNotExist:
            # Профиль не найден, создаем новый с ролью студента по умолчанию
            print(f"DEBUG Signal: Creating missing profile for user {instance.username}")
            Profile.objects.create(user=instance, role=Profile.STUDENT)

@receiver(post_save, sender=CustomUser)
def create_user_interface(sender, instance, created, **kwargs):
    """Создает настройки интерфейса при создании нового пользователя"""
    if created:
        UserInterface.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_interface(sender, instance, **kwargs):
    """Сохраняет настройки интерфейса при обновлении пользователя"""
    try:
        instance.interface.save()
    except UserInterface.DoesNotExist:
        UserInterface.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Отправляет приветственное уведомление пользователю в зависимости от его роли"""
    # Если профиль был только что создан - отправляем уведомление
    # Иначе (при обновлениях) не отправляем дополнительных уведомлений
    if not created:
        return None
        
    # Получаем пользователя и его полное имя
    user = instance.user
    full_name = user.get_full_name() or user.username
    
    # Проверяем наличие приветственных уведомлений для этого пользователя
    if Notification.objects.filter(
        user=user,
        title__startswith="Добро пожаловать"
    ).exists():
        # Если уже есть приветственное уведомление, не создаем новое
        print(f"DEBUG Signal: Welcome notification already exists for {user.username}")
        return None
    
    # Подготовка сообщений в зависимости от роли
    if instance.role == Profile.STUDENT:
        title = "Добро пожаловать на платформу!"
        message = f"Здравствуйте, {full_name}! Мы рады приветствовать вас на нашей образовательной платформе. "\
                 f"Здесь вы можете изучать курсы, выполнять задания и развивать свои навыки программирования. "\
                 f"Желаем вам успехов в обучении!"
        icon = "fa-graduation-cap"
    
    elif instance.role == Profile.TEACHER:
        title = "Добро пожаловать на платформу!"
        message = f"Здравствуйте, {full_name}! Рады приветствовать вас на нашей образовательной платформе. "\
                 f"Как преподаватель, вы можете создавать курсы, уроки и задания для студентов. "\
                 f"Мы надеемся, что платформа будет полезна в вашей педагогической деятельности!"
        icon = "fa-chalkboard-teacher"
    
    elif instance.role == Profile.ADMIN:
        title = "Добро пожаловать, администратор!"
        message = f"Здравствуйте, {full_name}! Вы были зарегистрированы как администратор платформы. "\
                 f"Вам доступны все функции управления, включая модерацию контента, управление пользователями "\
                 f"и настройку системы. Благодарим за вашу работу!"
        icon = "fa-user-shield"
    
    else:
        # Для неизвестных ролей используем общее сообщение
        title = "Добро пожаловать на платформу!"
        message = f"Здравствуйте, {full_name}! Спасибо за регистрацию на нашей образовательной платформе. "\
                 f"Мы рады видеть вас в нашем сообществе!"
        icon = "fa-user"
    
    # Создаем уведомление
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type='info',
        is_read=False,
        is_high_priority=True,
        url='/',
        importance='high',
        icon=icon
    )
    
    print(f"DEBUG Signal: Created welcome notification for {user.username} with role {instance.role}")
    return notification
