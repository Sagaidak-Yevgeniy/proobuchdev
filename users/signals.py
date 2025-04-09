from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, UserInterface
from notifications.models import Notification

# Переменная для контроля отключения сигналов
DISABLE_SIGNALS = False

@receiver(post_save, sender=CustomUser)
def create_user_interface(sender, instance, created, **kwargs):
    """Создает настройки интерфейса при создании нового пользователя"""
    if created and not DISABLE_SIGNALS:
        # Проверяем, существуют ли уже настройки интерфейса
        if not UserInterface.objects.filter(user=instance).exists():
            UserInterface.objects.create(user=instance)
            print(f"DEBUG Signal: Created user interface settings for {instance.username}")

@receiver(post_save, sender=Profile)
def send_welcome_notification(sender, instance, created, **kwargs):
    """Отправляет приветственное уведомление пользователю в зависимости от его роли"""
    # Если сигналы отключены или это не новый профиль, не отправляем уведомление
    if DISABLE_SIGNALS or not created:
        return None
        
    # Получаем пользователя и его полное имя
    user = instance.user
    full_name = user.get_full_name() or user.username
    
    # Проверяем наличие любых приветственных уведомлений для этого пользователя
    if Notification.objects.filter(
        user=user,
        title__startswith="Добро пожаловать"
    ).exists():
        # Если уже есть приветственное уведомление, удаляем его и создаем новое
        # соответствующее текущей роли пользователя
        print(f"DEBUG Signal: Deleting existing welcome notifications for {user.username}")
        Notification.objects.filter(
            user=user,
            title__startswith="Добро пожаловать"
        ).delete()
    
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
