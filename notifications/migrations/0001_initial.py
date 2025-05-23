# Generated by Django 5.2 on 2025-04-09 07:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receive_all', models.BooleanField(default=True, help_text='Если отключено, уведомления не будут отображаться', verbose_name='Получать все уведомления')),
                ('notify_only_high_priority', models.BooleanField(default=False, help_text='Если включено, будут приходить только важные уведомления', verbose_name='Только важные уведомления')),
                ('receive_achievement', models.BooleanField(default=True, help_text='Получать уведомления о новых достижениях и значках', verbose_name='Уведомления о достижениях')),
                ('receive_course', models.BooleanField(default=True, help_text='Получать уведомления об обновлениях курсов', verbose_name='Уведомления о курсах')),
                ('receive_lesson', models.BooleanField(default=True, help_text='Получать уведомления о новых и обновленных уроках', verbose_name='Уведомления об уроках')),
                ('receive_assignment', models.BooleanField(default=True, help_text='Получать уведомления о статусе заданий', verbose_name='Уведомления о заданиях')),
                ('receive_message', models.BooleanField(default=True, help_text='Получать уведомления о новых сообщениях', verbose_name='Уведомления о сообщениях')),
                ('email_notifications', models.BooleanField(default=False, help_text='Получать уведомления на email', verbose_name='Email-уведомления')),
                ('email_digest', models.BooleanField(default=True, help_text='Объединять уведомления в одно письмо (раз в день)', verbose_name='Дайджест писем')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_settings', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Настройки уведомлений',
                'verbose_name_plural': 'Настройки уведомлений',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('message', models.TextField(verbose_name='Сообщение')),
                ('notification_type', models.CharField(choices=[('info', 'Информация'), ('success', 'Успех'), ('warning', 'Предупреждение'), ('error', 'Ошибка'), ('achievement', 'Достижение'), ('course', 'Курс'), ('lesson', 'Урок'), ('assignment', 'Задание'), ('message', 'Сообщение'), ('system', 'Системное')], default='info', max_length=20, verbose_name='Тип уведомления')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('is_high_priority', models.BooleanField(default=False, verbose_name='Высокий приоритет')),
                ('url', models.CharField(blank=True, max_length=255, null=True, verbose_name='URL')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID объекта')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype', verbose_name='Тип контента')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'is_read', 'created_at'], name='notificatio_user_id_8a7c6b_idx'), models.Index(fields=['content_type', 'object_id'], name='notificatio_content_702c56_idx')],
            },
        ),
    ]
