import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model

from courses.models import Course

User = get_user_model()

class Olympiad(models.Model):
    """Модель олимпиады"""
    
    class OlympiadStatus(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        PUBLISHED = 'published', _('Опубликована')
        ACTIVE = 'active', _('Активна')
        COMPLETED = 'completed', _('Завершена')
        ARCHIVED = 'archived', _('В архиве')
    
    title = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Описание'))
    short_description = models.CharField(_('Краткое описание'), max_length=255, blank=True)
    image = models.ImageField(_('Изображение'), upload_to='olympiad_covers/', blank=True, null=True)
    start_datetime = models.DateTimeField(_('Дата и время начала'), default=timezone.now)
    end_datetime = models.DateTimeField(_('Дата и время окончания'), default=timezone.now)
    is_open = models.BooleanField(_('Открытая'), default=True, 
                                help_text=_('Если отмечено, любой пользователь может принять участие'))
    time_limit_minutes = models.PositiveIntegerField(_('Ограничение по времени (мин)'), 
                                                   default=0, 
                                                   help_text=_('0 означает без ограничения'))
    min_passing_score = models.PositiveIntegerField(_('Минимальный проходной балл'), default=0)
    invitation_code = models.CharField(_('Код приглашения'), max_length=20, blank=True, null=True, unique=True)
    
    status = models.CharField(_('Статус'), max_length=20, choices=OlympiadStatus.choices, default=OlympiadStatus.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  related_name='created_olympiads', verbose_name=_('Создатель'))
    participants = models.ManyToManyField(User, through='OlympiadParticipation', 
                                         related_name='olympiads', verbose_name=_('Участники'))
    
    is_rated = models.BooleanField(_('Рейтинговая'), default=True,
                               help_text=_('Влияет ли на общий рейтинг пользователей'))
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='olympiads', verbose_name=_('Связанный курс'))
    
    created_at = models.DateTimeField(_('Создана'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлена'), auto_now=True)
    
    class Meta:
        verbose_name = _('Олимпиада')
        verbose_name_plural = _('Олимпиады')
        ordering = ['-start_datetime']
    
    def __str__(self):
        return self.title
    
    def is_active(self):
        """Проверяет, активна ли олимпиада в текущий момент времени"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime and self.status == self.OlympiadStatus.ACTIVE
    
    def is_completed(self):
        """Проверяет, завершена ли олимпиада"""
        return self.end_datetime < timezone.now() or self.status == self.OlympiadStatus.COMPLETED
    
    def is_upcoming(self):
        """Проверяет, ожидается ли начало олимпиады"""
        return self.start_datetime > timezone.now() and self.status == self.OlympiadStatus.PUBLISHED
        
    def has_started(self):
        """Проверяет, началась ли олимпиада (но не обязательно активна)"""
        return self.start_datetime <= timezone.now()
    
    def get_or_create_invitation(self):
        """Получает или создает приглашение на олимпиаду на основе invitation_code"""
        # Если код приглашения не задан, генерируем его
        if not self.invitation_code:
            self.invitation_code = str(uuid.uuid4()).replace('-', '')[:20]
            self.save(update_fields=['invitation_code'])
        
        # Ищем или создаем приглашение
        invitation, created = OlympiadInvitation.objects.get_or_create(
            olympiad=self,
            code=self.invitation_code,
            defaults={
                'description': f'Основное приглашение для {self.title}',
                'is_active': True
            }
        )
        
        return invitation
        
    def can_participate(self, user):
        """Определяет, может ли пользователь участвовать в олимпиаде"""
        # Проверяем, что олимпиада активна
        if not self.is_active():
            return False
        
        # Проверяем, что олимпиада открытая или пользователь приглашен
        if not self.is_open:
            return OlympiadInvitation.objects.filter(olympiad=self, user=user, is_accepted=True).exists()
        
        # Проверяем, что пользователь еще не начал олимпиаду, или еще не истекло время
        participation = OlympiadParticipation.objects.filter(olympiad=self, user=user).first()
        if participation and participation.is_completed:
            return False
        
        # Если установлен лимит времени, проверяем, не истекло ли время
        if participation and self.time_limit_minutes > 0:
            time_passed = (timezone.now() - participation.started_at).total_seconds() / 60
            if time_passed >= self.time_limit_minutes:
                participation.is_completed = True
                participation.save()
                return False
        
        return True


class OlympiadTask(models.Model):
    """Модель задания олимпиады"""
    
    class TaskType(models.TextChoices):
        PROGRAMMING = 'programming', _('Программирование')
        MULTIPLE_CHOICE = 'multiple_choice', _('Тест с выбором ответа')
        THEORETICAL = 'theoretical', _('Теоретический вопрос')
    
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, 
                               related_name='tasks', verbose_name=_('Олимпиада'))
    title = models.CharField(_('Название'), max_length=255)
    description = models.TextField(_('Условие задачи'))
    task_type = models.CharField(_('Тип задания'), max_length=20, choices=TaskType.choices)
    
    points = models.PositiveIntegerField(_('Баллы'), default=1)
    time_limit_minutes = models.PositiveIntegerField(_('Ограничение по времени (мин)'), default=0,
                                                  help_text=_('0 означает без ограничения'))
    memory_limit_mb = models.PositiveIntegerField(_('Ограничение по памяти (МБ)'), default=0,
                                               help_text=_('0 означает без ограничения'))
    
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    min_passing_score = models.PositiveIntegerField(_('Минимальный проходной балл'), default=0)
    max_attempts = models.PositiveIntegerField(_('Максимальное количество попыток'), default=0,
                                            help_text=_('0 означает без ограничения'))
    
    initial_code = models.TextField(_('Начальный код'), blank=True,
                                 help_text=_('Код, который будет предоставлен участнику в начале'))
    
    # Дополнительные поля для связей
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, 
                             null=True, blank=True, 
                             related_name='olympiad_tasks', 
                             verbose_name=_('Связанный курс'))
    
    topic = models.CharField(_('Тема'), max_length=255, blank=True,
                           help_text=_('Тематика задания для группировки'))
    
    difficulty = models.PositiveSmallIntegerField(_('Сложность'), default=1,
                                               help_text=_('Уровень сложности от 1 до 5'))
    
    # Опции отображения и форматирования
    use_markdown = models.BooleanField(_('Использовать Markdown'), default=True,
                                    help_text=_('Отображать описание с поддержкой Markdown'))
    
    use_latex = models.BooleanField(_('Использовать LaTeX'), default=False,
                                   help_text=_('Включить поддержку математических формул в формате LaTeX'))
    
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('Задание олимпиады')
        verbose_name_plural = _('Задания олимпиад')
        ordering = ['olympiad', 'order']
    
    def __str__(self):
        return f"{self.olympiad.title} - {self.title}"


class OlympiadTestCase(models.Model):
    """Модель тестового случая для задания олимпиады"""
    
    task = models.ForeignKey(OlympiadTask, on_delete=models.CASCADE, 
                          related_name='test_cases', verbose_name=_('Задание'))
    input_data = models.TextField(_('Входные данные'))
    expected_output = models.TextField(_('Ожидаемый результат'))
    is_hidden = models.BooleanField(_('Скрытый тест'), default=False,
                                help_text=_('Если отмечено, данные теста не будут видны участнику'))
    explanation = models.TextField(_('Пояснение'), blank=True)
    points = models.PositiveIntegerField(_('Баллы за прохождение'), default=1)
    
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)
    
    class Meta:
        verbose_name = _('Тестовый случай')
        verbose_name_plural = _('Тестовые случаи')
        ordering = ['task', 'order']
    
    def __str__(self):
        return f"{self.task.title} - Тест #{self.order}"


class OlympiadMultipleChoiceOption(models.Model):
    """Модель варианта ответа для тестового задания олимпиады"""
    
    task = models.ForeignKey(OlympiadTask, on_delete=models.CASCADE,
                          related_name='options', verbose_name=_('Задание'))
    text = models.TextField(_('Текст варианта'))
    is_correct = models.BooleanField(_('Правильный ответ'), default=False)
    explanation = models.TextField(_('Пояснение'), blank=True)
    
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    
    created_at = models.DateTimeField(_('Создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлен'), auto_now=True)
    
    class Meta:
        verbose_name = _('Вариант ответа')
        verbose_name_plural = _('Варианты ответов')
        ordering = ['task', 'order']
    
    def __str__(self):
        return f"{self.task.title} - {self.text[:30]}{'...' if len(self.text) > 30 else ''}"


class OlympiadParticipation(models.Model):
    """Модель участия в олимпиаде"""
    
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE,
                               related_name='participations', verbose_name=_('Олимпиада'))
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                           related_name='olympiad_participations', verbose_name=_('Участник'))
    
    started_at = models.DateTimeField(_('Время начала'), auto_now_add=True)
    finished_at = models.DateTimeField(_('Время окончания'), null=True, blank=True)
    
    score = models.PositiveIntegerField(_('Набранные баллы'), default=0)
    max_score = models.PositiveIntegerField(_('Максимальные баллы'), default=0)
    is_completed = models.BooleanField(_('Завершил'), default=False)
    passed = models.BooleanField(_('Сдал'), default=False)
    
    class Meta:
        verbose_name = _('Участие в олимпиаде')
        verbose_name_plural = _('Участия в олимпиадах')
        unique_together = ['olympiad', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.olympiad.title}"
    
    def calculate_score(self):
        """Рассчитывает общий балл участника на основе выполненных заданий"""
        total_score = 0
        task_submissions = OlympiadTaskSubmission.objects.filter(
            participation=self,
            is_correct=True
        )
        
        for submission in task_submissions:
            total_score += submission.score
        
        self.score = total_score
        self.passed = total_score >= self.olympiad.min_passing_score
        self.save()
        
        return total_score


class OlympiadTaskSubmission(models.Model):
    """Модель отправки решения задания олимпиады"""
    
    participation = models.ForeignKey(OlympiadParticipation, on_delete=models.CASCADE,
                                    related_name='submissions', verbose_name=_('Участие'))
    task = models.ForeignKey(OlympiadTask, on_delete=models.CASCADE,
                          related_name='submissions', verbose_name=_('Задание'))
    
    code = models.TextField(_('Код решения'), blank=True)
    text_answer = models.TextField(_('Текстовый ответ'), blank=True)
    selected_options = models.ManyToManyField(OlympiadMultipleChoiceOption, 
                                           blank=True,
                                           related_name='submissions',
                                           verbose_name=_('Выбранные варианты'))
    
    score = models.PositiveIntegerField(_('Набранные баллы'), default=0)
    max_score = models.PositiveIntegerField(_('Максимальные баллы'), default=0)
    is_correct = models.BooleanField(_('Правильное решение'), default=False)
    
    # Для программирования - результаты тестирования
    passed_test_cases = models.PositiveIntegerField(_('Пройдено тестов'), default=0)
    total_test_cases = models.PositiveIntegerField(_('Всего тестов'), default=0)
    
    # Информация для отладки
    execution_time = models.FloatField(_('Время выполнения (сек)'), default=0)
    memory_usage = models.FloatField(_('Использовано памяти (МБ)'), default=0)
    error_message = models.TextField(_('Сообщение об ошибке'), blank=True)
    
    submitted_at = models.DateTimeField(_('Время отправки'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Отправка решения')
        verbose_name_plural = _('Отправки решений')
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.participation.user.username} - {self.task.title}"


class OlympiadUserInvitation(models.Model):
    """Модель приглашения на участие в закрытой олимпиаде для конкретного пользователя"""
    
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE,
                               related_name='user_invitations', verbose_name=_('Олимпиада'))
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                           related_name='olympiad_invitations', verbose_name=_('Пользователь'))
    
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='sent_olympiad_invitations', verbose_name=_('Пригласил'))
    
    is_accepted = models.BooleanField(_('Принято'), default=False)
    
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Обновлено'), auto_now=True)
    
    class Meta:
        verbose_name = _('Приглашение пользователю')
        verbose_name_plural = _('Приглашения пользователям')
        unique_together = ['olympiad', 'user']
    
    def __str__(self):
        return f"{self.olympiad.title} - {self.user.username}"


class OlympiadInvitation(models.Model):
    """Модель для ссылок-приглашений на олимпиаду"""
    
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE,
                               related_name='invitations', verbose_name=_('Олимпиада'))
    
    code = models.CharField(_('Код приглашения'), max_length=32, unique=True, default='00000000000000000000000000000000')
    description = models.CharField(_('Описание'), max_length=255, blank=True)
    
    is_active = models.BooleanField(_('Активно'), default=True)
    max_uses = models.PositiveIntegerField(_('Максимальное количество использований'), default=0,
                                          help_text=_('0 означает без ограничений'))
    used_count = models.PositiveIntegerField(_('Использовано'), default=0)
    
    expires_at = models.DateTimeField(_('Срок действия до'), null=True, blank=True)
    created_at = models.DateTimeField(_('Создано'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Приглашение на олимпиаду')
        verbose_name_plural = _('Приглашения на олимпиаду')
    
    def __str__(self):
        return f"{self.olympiad.title} - {self.code}"
    
    def is_valid(self):
        """Проверяет, действительно ли приглашение"""
        if not self.is_active:
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        
        return True
    
    def get_absolute_url(self):
        """Возвращает URL для приглашения"""
        from django.urls import reverse
        return reverse('olympiads:olympiad_join_by_invitation', kwargs={'code': self.code})
    
    def use(self):
        """Увеличивает счетчик использований приглашения"""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class OlympiadCertificate(models.Model):
    """Модель сертификата за прохождение олимпиады"""
    
    participation = models.OneToOneField(OlympiadParticipation, on_delete=models.CASCADE,
                                       related_name='certificate', verbose_name=_('Участие'))
    
    certificate_id = models.CharField(_('Номер сертификата'), max_length=255, unique=True)
    certificate_file = models.FileField(_('Файл сертификата'), upload_to='olympiad_certificates/')
    
    issue_date = models.DateTimeField(_('Дата выдачи'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Сертификат олимпиады')
        verbose_name_plural = _('Сертификаты олимпиад')
    
    def __str__(self):
        return f"Сертификат {self.certificate_id} - {self.participation.user.username}"