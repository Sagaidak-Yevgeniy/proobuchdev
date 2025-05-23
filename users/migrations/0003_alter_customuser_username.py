# Generated by Django 5.2 on 2025-04-09 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_userinterface'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(error_messages={'unique': 'Пользователь с таким ФИО уже существует.'}, help_text='Введите полное ФИО. Будет использоваться для входа.', max_length=150, unique=True, verbose_name='username'),
        ),
    ]
