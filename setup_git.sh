#!/bin/bash

# Инициализация Git-репозитория
git init

# Добавление всех файлов (кроме игнорируемых в .gitignore)
git add .

# Проверка статуса
git status

echo "Git репозиторий инициализирован. Теперь вы можете выполнить:"
echo "git commit -m 'Начальная версия проекта'"
echo "git remote add origin https://github.com/ваш-пользователь/ваш-репозиторий.git"
echo "git push -u origin master"