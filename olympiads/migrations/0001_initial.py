# Generated by Django 5.2 on 2025-04-09 15:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Olympiad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название олимпиады')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='URL')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('start_time', models.DateTimeField(verbose_name='Время начала')),
                ('end_time', models.DateTimeField(verbose_name='Время окончания')),
                ('is_published', models.BooleanField(default=False, verbose_name='Опубликована')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_olympiads', to=settings.AUTH_USER_MODEL, verbose_name='Создатель')),
            ],
            options={
                'verbose_name': 'Олимпиада',
                'verbose_name_plural': 'Олимпиады',
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название задачи')),
                ('description', models.TextField(verbose_name='Условие задачи')),
                ('time_limit', models.PositiveIntegerField(default=1000, verbose_name='Ограничение по времени (мс)')),
                ('memory_limit', models.PositiveIntegerField(default=256, verbose_name='Ограничение по памяти (МБ)')),
                ('points', models.PositiveIntegerField(default=100, verbose_name='Баллы за решение')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядковый номер')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='olympiads.olympiad', verbose_name='Олимпиада')),
            ],
            options={
                'verbose_name': 'Задача',
                'verbose_name_plural': 'Задачи',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField(verbose_name='Код решения')),
                ('status', models.CharField(choices=[('pending', 'В обработке'), ('testing', 'Тестируется'), ('accepted', 'Принято'), ('wrong_answer', 'Неправильный ответ'), ('time_limit', 'Превышено время выполнения'), ('memory_limit', 'Превышен лимит памяти'), ('runtime_error', 'Ошибка выполнения'), ('compilation_error', 'Ошибка компиляции'), ('system_error', 'Системная ошибка')], default='pending', max_length=20, verbose_name='Статус')),
                ('points', models.PositiveIntegerField(default=0, verbose_name='Набранные баллы')),
                ('executed_time', models.PositiveIntegerField(blank=True, null=True, verbose_name='Время выполнения (мс)')),
                ('error_message', models.TextField(blank=True, verbose_name='Сообщение об ошибке')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='Время отправки')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='olympiads.olympiad', verbose_name='Олимпиада')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='olympiads.problem', verbose_name='Задача')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='olympiad_submissions', to=settings.AUTH_USER_MODEL, verbose_name='Участник')),
            ],
            options={
                'verbose_name': 'Отправка решения',
                'verbose_name_plural': 'Отправки решений',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_data', models.TextField(verbose_name='Входные данные')),
                ('expected_output', models.TextField(verbose_name='Ожидаемый результат')),
                ('is_example', models.BooleanField(default=False, verbose_name='Пример для отображения')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядковый номер')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_cases', to='olympiads.problem', verbose_name='Задача')),
            ],
            options={
                'verbose_name': 'Тестовый случай',
                'verbose_name_plural': 'Тестовые случаи',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('passed', models.BooleanField(default=False, verbose_name='Пройден')),
                ('execution_time', models.PositiveIntegerField(blank=True, null=True, verbose_name='Время выполнения (мс)')),
                ('memory_used', models.PositiveIntegerField(blank=True, null=True, verbose_name='Использовано памяти (КБ)')),
                ('output', models.TextField(blank=True, verbose_name='Вывод решения')),
                ('error_message', models.TextField(blank=True, verbose_name='Сообщение об ошибке')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='olympiads.submission', verbose_name='Отправка')),
                ('test_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_results', to='olympiads.testcase', verbose_name='Тестовый случай')),
            ],
            options={
                'verbose_name': 'Результат теста',
                'verbose_name_plural': 'Результаты тестов',
                'ordering': ['test_case__order'],
            },
        ),
        migrations.CreateModel(
            name='OlympiadParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_at', models.DateTimeField(auto_now_add=True, verbose_name='Время регистрации')),
                ('total_points', models.PositiveIntegerField(default=0, verbose_name='Общее количество баллов')),
                ('solved_problems', models.PositiveIntegerField(default=0, verbose_name='Решено задач')),
                ('olympiad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='olympiads.olympiad', verbose_name='Олимпиада')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participating_olympiads', to=settings.AUTH_USER_MODEL, verbose_name='Участник')),
            ],
            options={
                'verbose_name': 'Участник олимпиады',
                'verbose_name_plural': 'Участники олимпиады',
                'ordering': ['-total_points', 'solved_problems'],
                'unique_together': {('olympiad', 'user')},
            },
        ),
    ]
