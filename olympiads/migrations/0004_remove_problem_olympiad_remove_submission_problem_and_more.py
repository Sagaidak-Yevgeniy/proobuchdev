# Generated by Django 5.2 on 2025-04-10 08:02

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_certificatetemplate_course_difficulty_level_and_more'),
        ('olympiads', '0003_alter_submission_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='olympiad',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='problem',
        ),
        migrations.RemoveField(
            model_name='testcase',
            name='problem',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='olympiad',
        ),
        migrations.RemoveField(
            model_name='submission',
            name='user',
        ),
        migrations.RemoveField(
            model_name='testresult',
            name='submission',
        ),
        migrations.RemoveField(
            model_name='testresult',
            name='test_case',
        ),
        migrations.AlterModelOptions(
            name='olympiad',
            options={'ordering': ['-start_datetime'], 'verbose_name': 'Олимпиада', 'verbose_name_plural': 'Олимпиады'},
        ),
        migrations.RemoveField(
            model_name='olympiad',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='olympiad',
            name='end_time',
        ),
        migrations.RemoveField(
            model_name='olympiad',
            name='is_published',
        ),
        migrations.RemoveField(
            model_name='olympiad',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='olympiad',
            name='start_time',
        ),
        migrations.AddField(
            model_name='olympiad',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_olympiads', to=settings.AUTH_USER_MODEL, verbose_name='Создатель'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='end_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата и время окончания'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='olympiad_covers/', verbose_name='Изображение'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='is_open',
            field=models.BooleanField(default=True, help_text='Если отмечено, любой пользователь может принять участие', verbose_name='Открытая'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='is_rated',
            field=models.BooleanField(default=True, help_text='Влияет ли на общий рейтинг пользователей', verbose_name='Рейтинговая'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='min_passing_score',
            field=models.PositiveIntegerField(default=0, verbose_name='Минимальный проходной балл'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='related_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='olympiads', to='courses.course', verbose_name='Связанный курс'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='short_description',
            field=models.CharField(blank=True, max_length=255, verbose_name='Краткое описание'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='start_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата и время начала'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='status',
            field=models.CharField(choices=[('draft', 'Черновик'), ('published', 'Опубликована'), ('active', 'Активна'), ('completed', 'Завершена'), ('archived', 'В архиве')], default='draft', max_length=20, verbose_name='Статус'),
        ),
        migrations.AddField(
            model_name='olympiad',
            name='time_limit_minutes',
            field=models.PositiveIntegerField(default=0, help_text='0 означает без ограничения', verbose_name='Ограничение по времени (мин)'),
        ),
        migrations.AlterField(
            model_name='olympiad',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Создана'),
        ),
        migrations.AlterField(
            model_name='olympiad',
            name='description',
            field=models.TextField(verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='olympiad',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='olympiad',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлена'),
        ),
        migrations.CreateModel(
            name='OlympiadInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='Принято')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_olympiad_invitations', to=settings.AUTH_USER_MODEL, verbose_name='Пригласил')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='olympiads.olympiad', verbose_name='Олимпиада')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='olympiad_invitations', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Приглашение на олимпиаду',
                'verbose_name_plural': 'Приглашения на олимпиады',
                'unique_together': {('olympiad', 'user')},
            },
        ),
        migrations.CreateModel(
            name='OlympiadParticipation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True, verbose_name='Время начала')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='Время окончания')),
                ('score', models.PositiveIntegerField(default=0, verbose_name='Набранные баллы')),
                ('max_score', models.PositiveIntegerField(default=0, verbose_name='Максимальные баллы')),
                ('is_completed', models.BooleanField(default=False, verbose_name='Завершил')),
                ('passed', models.BooleanField(default=False, verbose_name='Сдал')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participations', to='olympiads.olympiad', verbose_name='Олимпиада')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='olympiad_participations', to=settings.AUTH_USER_MODEL, verbose_name='Участник')),
            ],
            options={
                'verbose_name': 'Участие в олимпиаде',
                'verbose_name_plural': 'Участия в олимпиадах',
                'unique_together': {('olympiad', 'user')},
            },
        ),
        migrations.CreateModel(
            name='OlympiadCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate_id', models.CharField(max_length=255, unique=True, verbose_name='Номер сертификата')),
                ('certificate_file', models.FileField(upload_to='olympiad_certificates/', verbose_name='Файл сертификата')),
                ('issue_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')),
                ('participation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='certificate', to='olympiads.olympiadparticipation', verbose_name='Участие')),
            ],
            options={
                'verbose_name': 'Сертификат олимпиады',
                'verbose_name_plural': 'Сертификаты олимпиад',
            },
        ),
        migrations.AddField(
            model_name='olympiad',
            name='participants',
            field=models.ManyToManyField(related_name='olympiads', through='olympiads.OlympiadParticipation', to=settings.AUTH_USER_MODEL, verbose_name='Участники'),
        ),
        migrations.CreateModel(
            name='OlympiadTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Условие задачи')),
                ('task_type', models.CharField(choices=[('programming', 'Программирование'), ('multiple_choice', 'Тест с выбором ответа'), ('theoretical', 'Теоретический вопрос')], max_length=20, verbose_name='Тип задания')),
                ('points', models.PositiveIntegerField(default=1, verbose_name='Баллы')),
                ('time_limit_minutes', models.PositiveIntegerField(default=0, help_text='0 означает без ограничения', verbose_name='Ограничение по времени (мин)')),
                ('memory_limit_mb', models.PositiveIntegerField(default=0, help_text='0 означает без ограничения', verbose_name='Ограничение по памяти (МБ)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('min_passing_score', models.PositiveIntegerField(default=0, verbose_name='Минимальный проходной балл')),
                ('initial_code', models.TextField(blank=True, help_text='Код, который будет предоставлен участнику в начале', verbose_name='Начальный код')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='olympiads.olympiad', verbose_name='Олимпиада')),
            ],
            options={
                'verbose_name': 'Задание олимпиады',
                'verbose_name_plural': 'Задания олимпиад',
                'ordering': ['olympiad', 'order'],
            },
        ),
        migrations.CreateModel(
            name='OlympiadMultipleChoiceOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст варианта')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильный ответ')),
                ('explanation', models.TextField(blank=True, verbose_name='Пояснение')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлен')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='olympiads.olympiadtask', verbose_name='Задание')),
            ],
            options={
                'verbose_name': 'Вариант ответа',
                'verbose_name_plural': 'Варианты ответов',
                'ordering': ['task', 'order'],
            },
        ),
        migrations.CreateModel(
            name='OlympiadTaskSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField(blank=True, verbose_name='Код решения')),
                ('text_answer', models.TextField(blank=True, verbose_name='Текстовый ответ')),
                ('score', models.PositiveIntegerField(default=0, verbose_name='Набранные баллы')),
                ('max_score', models.PositiveIntegerField(default=0, verbose_name='Максимальные баллы')),
                ('is_correct', models.BooleanField(default=False, verbose_name='Правильное решение')),
                ('passed_test_cases', models.PositiveIntegerField(default=0, verbose_name='Пройдено тестов')),
                ('total_test_cases', models.PositiveIntegerField(default=0, verbose_name='Всего тестов')),
                ('execution_time', models.FloatField(default=0, verbose_name='Время выполнения (сек)')),
                ('memory_usage', models.FloatField(default=0, verbose_name='Использовано памяти (МБ)')),
                ('error_message', models.TextField(blank=True, verbose_name='Сообщение об ошибке')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')),
                ('participation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='olympiads.olympiadparticipation', verbose_name='Участие')),
                ('selected_options', models.ManyToManyField(blank=True, related_name='submissions', to='olympiads.olympiadmultiplechoiceoption', verbose_name='Выбранные варианты')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='olympiads.olympiadtask', verbose_name='Задание')),
            ],
            options={
                'verbose_name': 'Отправка решения',
                'verbose_name_plural': 'Отправки решений',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='OlympiadTestCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_data', models.TextField(verbose_name='Входные данные')),
                ('expected_output', models.TextField(verbose_name='Ожидаемый результат')),
                ('is_hidden', models.BooleanField(default=False, help_text='Если отмечено, данные теста не будут видны участнику', verbose_name='Скрытый тест')),
                ('explanation', models.TextField(blank=True, verbose_name='Пояснение')),
                ('points', models.PositiveIntegerField(default=1, verbose_name='Баллы за прохождение')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлен')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_cases', to='olympiads.olympiadtask', verbose_name='Задание')),
            ],
            options={
                'verbose_name': 'Тестовый случай',
                'verbose_name_plural': 'Тестовые случаи',
                'ordering': ['task', 'order'],
            },
        ),
        migrations.DeleteModel(
            name='OlympiadParticipant',
        ),
        migrations.DeleteModel(
            name='Problem',
        ),
        migrations.DeleteModel(
            name='Submission',
        ),
        migrations.DeleteModel(
            name='TestCase',
        ),
        migrations.DeleteModel(
            name='TestResult',
        ),
    ]
