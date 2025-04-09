from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.conf import settings


class Olympiad(models.Model):
    """Модель олимпиады с набором задач и временными рамками проведения"""
    title = models.CharField('Название олимпиады', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)
    start_time = models.DateTimeField('Время начала')
    end_time = models.DateTimeField('Время окончания')
    is_published = models.BooleanField('Опубликована', default=False)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_olympiads',
        verbose_name='Создатель'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Олимпиада'
        verbose_name_plural = 'Олимпиады'
        ordering = ['-start_time']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем slug при первом сохранении
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('olympiad_detail', kwargs={'slug': self.slug})
    
    def is_active(self):
        """Проверяет, активна ли олимпиада (идет ли она сейчас)"""
        now = timezone.now()
        return self.start_time <= now and self.end_time >= now
    
    def is_future(self):
        """Проверяет, запланирована ли олимпиада на будущее"""
        return self.start_time > timezone.now()
    
    def is_past(self):
        """Проверяет, завершена ли олимпиада"""
        return self.end_time < timezone.now()
    
    @property
    def status(self):
        """Возвращает статус олимпиады: активная/предстоящая/завершенная/черновик"""
        if not self.is_published:
            return 'draft'
        if self.is_active():
            return 'active'
        if self.is_future():
            return 'future'
        return 'past'
    
    @property
    def status_display(self):
        """Возвращает отображаемый статус олимпиады на русском"""
        status_dict = {
            'draft': 'Черновик',
            'active': 'Активная',
            'future': 'Предстоящая',
            'past': 'Завершена'
        }
        return status_dict.get(self.status, 'Неизвестно')
    
    @property
    def problems_count(self):
        """Возвращает количество задач в олимпиаде"""
        return self.problems.count()
    
    @property
    def participants_count(self):
        """Возвращает количество участников олимпиады"""
        return self.participants.count()


class Problem(models.Model):
    """Модель задачи в олимпиаде"""
    olympiad = models.ForeignKey(
        Olympiad,
        on_delete=models.CASCADE,
        related_name='problems',
        verbose_name='Олимпиада'
    )
    title = models.CharField('Название задачи', max_length=200)
    description = models.TextField('Условие задачи')
    time_limit = models.PositiveIntegerField('Ограничение по времени (мс)', default=1000)
    memory_limit = models.PositiveIntegerField('Ограничение по памяти (МБ)', default=256)
    points = models.PositiveIntegerField('Баллы за решение', default=100)
    order = models.PositiveIntegerField('Порядковый номер', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['order']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('problem_detail', kwargs={
            'olympiad_slug': self.olympiad.slug,
            'pk': self.pk
        })
    
    @property
    def total_test_cases(self):
        """Возвращает общее количество тестовых случаев для задачи"""
        return self.test_cases.count()


class TestCase(models.Model):
    """Модель тестового случая для задачи"""
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='Задача'
    )
    input_data = models.TextField('Входные данные')
    expected_output = models.TextField('Ожидаемый результат')
    is_example = models.BooleanField('Пример для отображения', default=False)
    weight = models.PositiveIntegerField('Вес теста', default=1,
                                        help_text='Относительный вес теста при подсчете баллов')
    order = models.PositiveIntegerField('Порядковый номер', default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Тестовый случай'
        verbose_name_plural = 'Тестовые случаи'
        ordering = ['order']
    
    def __str__(self):
        return f"Тест {self.order} для задачи {self.problem.title}"


class Submission(models.Model):
    """Модель отправки решения задачи участником"""
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('testing', 'Тестируется'),
        ('accepted', 'Принято'),
        ('wrong_answer', 'Неправильный ответ'),
        ('time_limit', 'Превышено время выполнения'),
        ('memory_limit', 'Превышен лимит памяти'),
        ('runtime_error', 'Ошибка выполнения'),
        ('compilation_error', 'Ошибка компиляции'),
        ('system_error', 'Системная ошибка'),
    ]
    
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Задача'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='olympiad_submissions',
        verbose_name='Участник'
    )
    olympiad = models.ForeignKey(
        Olympiad,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Олимпиада'
    )
    code = models.TextField('Код решения')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    points = models.PositiveIntegerField('Набранные баллы', default=0)
    executed_time = models.PositiveIntegerField('Время выполнения (мс)', null=True, blank=True)
    error_message = models.TextField('Сообщение об ошибке', blank=True)
    submitted_at = models.DateTimeField('Время отправки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отправка решения'
        verbose_name_plural = 'Отправки решений'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} ({self.status})"

    @property
    def status_display_color(self):
        """Возвращает цвет для отображения статуса"""
        color_map = {
            'pending': 'gray',
            'testing': 'blue',
            'accepted': 'green',
            'wrong_answer': 'red',
            'time_limit': 'orange',
            'memory_limit': 'orange',
            'runtime_error': 'red',
            'compilation_error': 'red',
            'system_error': 'purple',
        }
        return color_map.get(self.status, 'gray')


class TestResult(models.Model):
    """Модель результата прохождения отдельного тестового случая"""
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name='Отправка'
    )
    test_case = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name='Тестовый случай'
    )
    passed = models.BooleanField('Пройден', default=False)
    execution_time = models.PositiveIntegerField('Время выполнения (мс)', null=True, blank=True)
    memory_used = models.PositiveIntegerField('Использовано памяти (КБ)', null=True, blank=True)
    output = models.TextField('Вывод решения', blank=True)
    error_message = models.TextField('Сообщение об ошибке', blank=True)
    
    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        ordering = ['test_case__order']

    def __str__(self):
        status = 'Пройден' if self.passed else 'Не пройден'
        return f"Тест {self.test_case.order} - {status}"


class OlympiadParticipant(models.Model):
    """Модель участника олимпиады для отслеживания регистраций"""
    olympiad = models.ForeignKey(
        Olympiad,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='Олимпиада'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='participating_olympiads',
        verbose_name='Участник'
    )
    registered_at = models.DateTimeField('Время регистрации', auto_now_add=True)
    total_points = models.PositiveIntegerField('Общее количество баллов', default=0)
    solved_problems = models.PositiveIntegerField('Решено задач', default=0)
    
    class Meta:
        verbose_name = 'Участник олимпиады'
        verbose_name_plural = 'Участники олимпиады'
        unique_together = ['olympiad', 'user']
        ordering = ['-total_points', 'solved_problems']

    def __str__(self):
        return f"{self.user.username} - {self.olympiad.title}"

    def update_statistics(self):
        """Обновляет статистику участника по решенным задачам и набранным баллам"""
        # Получаем список успешно решенных задач
        from django.db.models import Max
        
        solved_problems = set()
        total_points = 0
        
        submissions = Submission.objects.filter(
            user=self.user,
            olympiad=self.olympiad
        )
        
        for problem in self.olympiad.problems.all():
            # Находим лучшую отправку для каждой задачи
            best_submission = submissions.filter(
                problem=problem,
                status='accepted'
            ).order_by('-points', 'submitted_at').first()
            
            if best_submission:
                solved_problems.add(best_submission.problem_id)
                total_points += best_submission.points
        
        self.solved_problems = len(solved_problems)
        self.total_points = total_points
        self.save()