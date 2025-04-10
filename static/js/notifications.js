/**
 * Скрипт для обработки уведомлений
 */

document.addEventListener('DOMContentLoaded', function() {
    // Элементы DOM
    const notificationButton = document.getElementById('notification-button');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const notificationList = document.getElementById('notification-list');
    const notificationNoItems = document.getElementById('notification-no-items');
    const markAllReadButton = document.getElementById('mark-all-as-read');
    const notificationCount = document.querySelector('.notification-count');
    
    if (!notificationButton) {
        // Если кнопки уведомлений нет на странице, выходим
        return;
    }
    
    // Показывает выпадающее меню
    function showDropdown() {
        // Позиционируем выпадающее меню
        positionDropdown();
        
        notificationDropdown.classList.remove('hidden');
        // Загружаем список уведомлений
        loadNotifications();
    }
    
    // Позиционирует выпадающее меню относительно кнопки
    function positionDropdown() {
        if (window.innerWidth < 640) {
            // На мобильных устройствах используем фиксированное позиционирование
            // Позиционирование задано через CSS классы в HTML
            
            // Устанавливаем максимальную высоту для мобильных устройств
            const maxHeight = window.innerHeight * 0.8; // 80% от высоты экрана
            notificationDropdown.style.maxHeight = `${maxHeight}px`;
            
            // Гарантируем, что на мобильных устройствах меню выровнено по правому краю
            notificationDropdown.style.left = 'auto';
            notificationDropdown.style.right = '8px'; // 2rem, соответствует right-2 в tailwind
            
            // Устанавливаем максимальную высоту для внутреннего контейнера с уведомлениями
            const listContainer = notificationDropdown.querySelector('.overflow-y-auto');
            if (listContainer) {
                listContainer.style.maxHeight = `${maxHeight - 120}px`; // за вычетом высоты шапки и футера
            }
            
            return;
        }
        
        // На десктопе используем абсолютное позиционирование
        notificationDropdown.style.maxHeight = '80vh';
        notificationDropdown.style.left = 'auto';
        notificationDropdown.style.right = '0';
        
        // Сбрасываем высоту внутреннего контейнера
        const listContainer = notificationDropdown.querySelector('.overflow-y-auto');
        if (listContainer) {
            listContainer.style.maxHeight = '60vh';
        }
    }
    
    // Скрывает выпадающее меню
    function hideDropdown() {
        notificationDropdown.classList.add('hidden');
        
        // Сбрасываем стили для плавного перехода при следующем открытии
        if (window.innerWidth < 640) {
            setTimeout(() => {
                notificationDropdown.style.maxHeight = '';
                const listContainer = notificationDropdown.querySelector('.overflow-y-auto');
                if (listContainer) {
                    listContainer.style.maxHeight = '';
                }
            }, 300);
        }
    }
    
    // Загружает список уведомлений через API
    function loadNotifications() {
        fetch('/notifications/list/?format=json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Сетевая ошибка');
                }
                return response.json();
            })
            .then(data => {
                // Очищаем список
                notificationList.innerHTML = '';
                
                if (!data.notifications || data.notifications.length === 0) {
                    // Если уведомлений нет, показываем сообщение "Нет уведомлений"
                    notificationNoItems.classList.remove('hidden');
                } else {
                    notificationNoItems.classList.add('hidden');
                    
                    // Добавляем уведомления в список
                    data.notifications.forEach(notification => {
                        const notificationItem = createNotificationItem(notification);
                        notificationList.appendChild(notificationItem);
                    });
                }
                
                // Обновляем счетчик непрочитанных уведомлений
                if (data.unread_count !== undefined) {
                    updateNotificationCount(data.unread_count);
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке списка уведомлений:', error);
                // Показываем сообщение об ошибке
                notificationList.innerHTML = '<li class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">Ошибка загрузки уведомлений</li>';
                notificationNoItems.classList.add('hidden');
            });
    }
    
    // Создает элемент уведомления
    function createNotificationItem(notification) {
        const li = document.createElement('li');
        li.classList.add('px-4', 'py-3', 'hover:bg-gray-50', 'dark:hover:bg-gray-700');
        if (!notification.is_read) {
            li.classList.add('bg-blue-50', 'dark:bg-blue-900/20');
        }
        
        // Формируем иконку в зависимости от типа уведомления
        let iconSvg = '';
        switch (notification.notification_type) {
            case 'info':
                iconSvg = '<svg class="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                break;
            case 'success':
                iconSvg = '<svg class="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                break;
            case 'warning':
                iconSvg = '<svg class="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>';
                break;
            case 'error':
                iconSvg = '<svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                break;
            case 'achievement':
                iconSvg = '<svg class="h-5 w-5 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>';
                break;
            case 'course':
                iconSvg = '<svg class="h-5 w-5 text-purple-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>';
                break;
            case 'lesson':
                iconSvg = '<svg class="h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>';
                break;
            case 'assignment':
                iconSvg = '<svg class="h-5 w-5 text-pink-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>';
                break;
            case 'message':
                iconSvg = '<svg class="h-5 w-5 text-teal-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>';
                break;
            default:
                iconSvg = '<svg class="h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>';
        }
        
        // Форматирование даты
        const date = new Date(notification.created_at);
        const formattedDate = formatDate(date);
        
        // Формируем HTML уведомления
        let html = `
            <div class="flex items-start flex-nowrap" data-id="${notification.id}">
                <div class="flex-shrink-0 mr-2">
                    ${iconSvg}
                </div>
                <div class="flex-1 min-w-0 overflow-hidden">
                    <div class="flex flex-col sm:flex-row sm:justify-between">
                        <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate mb-1 sm:mb-0 flex flex-wrap items-center">
                            <span class="mr-1">${notification.title}</span>
                            ${notification.is_high_priority ? '<span class="inline-flex items-center px-1 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Важно</span>' : ''}
                        </p>
                        <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap mb-1 sm:mb-0">
                            ${formattedDate}
                        </span>
                    </div>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2 break-words">
                        ${notification.message}
                    </p>
                    <div class="mt-2 flex flex-wrap justify-end gap-2">
                        ${!notification.is_read ? 
                            `<button class="mark-read-button text-xs text-blue-600 dark:text-blue-400 hover:underline" data-id="${notification.id}">
                                <i class="fas fa-check mr-1"></i> Прочитано
                            </button>` : ''}
                        <button class="delete-button text-xs text-red-600 dark:text-red-400 hover:underline" data-id="${notification.id}">
                            <i class="fas fa-trash-alt mr-1"></i> Удалить
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Если есть URL, обернем уведомление в ссылку
        if (notification.url) {
            html = `
                <a href="${notification.url}" class="block hover:no-underline">
                    ${html}
                </a>
            `;
        }
        
        li.innerHTML = html;
        
        // Добавляем обработчики событий для кнопок
        setTimeout(() => {
            const markReadButton = li.querySelector('.mark-read-button');
            if (markReadButton) {
                markReadButton.addEventListener('click', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    const id = this.dataset.id;
                    markAsRead(id);
                });
            }
            
            const deleteButton = li.querySelector('.delete-button');
            if (deleteButton) {
                deleteButton.addEventListener('click', function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                    const id = this.dataset.id;
                    deleteNotification(id);
                });
            }
        }, 0);
        
        return li;
    }
    
    // Форматирует дату в локальный формат
    function formatDate(date) {
        const now = new Date();
        const diff = now - date;
        
        // Если менее 24 часов назад, показываем относительное время
        if (diff < 24 * 60 * 60 * 1000) {
            // Если менее часа назад
            if (diff < 60 * 60 * 1000) {
                const mins = Math.floor(diff / (60 * 1000));
                return mins === 0 ? 'Только что' : `${mins} мин. назад`;
            } else {
                const hours = Math.floor(diff / (60 * 60 * 1000));
                return `${hours} ч. назад`;
            }
        } else {
            // Показываем дату
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
    
    // Отметка уведомления как прочитанное
    function markAsRead(id) {
        const csrfToken = getCsrfToken();
        
        fetch(`/notifications/read/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем внешний вид уведомления
                const notificationItems = notificationList.querySelectorAll(`[data-id="${id}"]`);
                notificationItems.forEach(item => {
                    const parent = item.closest('li');
                    if (parent) {
                        parent.classList.remove('bg-blue-50', 'dark:bg-blue-900/20');
                    }
                    
                    const markReadButton = item.querySelector('.mark-read-button');
                    if (markReadButton) {
                        markReadButton.remove();
                    }
                });
                
                // Обновляем счетчик непрочитанных уведомлений
                updateNotificationCount(data.unread_count);
            }
        })
        .catch(error => {
            console.error('Ошибка при отметке уведомления как прочитанного:', error);
        });
    }
    
    // Удаление уведомления
    function deleteNotification(id) {
        const csrfToken = getCsrfToken();
        
        fetch(`/notifications/delete/${id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Удаляем уведомление из DOM
                const notificationItems = notificationList.querySelectorAll(`[data-id="${id}"]`);
                notificationItems.forEach(item => {
                    const parent = item.closest('li');
                    if (parent) {
                        parent.remove();
                    }
                });
                
                // Обновляем счетчик непрочитанных уведомлений
                updateNotificationCount(data.unread_count);
                
                // Проверяем, остались ли еще уведомления
                if (notificationList.children.length === 0) {
                    notificationNoItems.classList.remove('hidden');
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении уведомления:', error);
        });
    }
    
    // Отметка всех уведомлений как прочитанные
    function markAllAsRead() {
        const csrfToken = getCsrfToken();
        
        fetch('/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем внешний вид всех уведомлений
                const items = notificationList.querySelectorAll('li');
                items.forEach(item => {
                    item.classList.remove('bg-blue-50', 'dark:bg-blue-900/20');
                    const markReadButton = item.querySelector('.mark-read-button');
                    if (markReadButton) {
                        markReadButton.remove();
                    }
                });
                
                // Обновляем счетчик непрочитанных уведомлений
                updateNotificationCount(0);
            }
        })
        .catch(error => {
            console.error('Ошибка при отметке всех уведомлений как прочитанных:', error);
        });
    }
    
    // Обновляет счетчик непрочитанных уведомлений
    function updateNotificationCount(count) {
        if (count > 0) {
            notificationCount.textContent = count > 99 ? '99+' : count;
            notificationCount.classList.remove('hidden');
        } else {
            notificationCount.classList.add('hidden');
        }
    }
    
    // Загружает количество непрочитанных уведомлений
    function loadNotificationCount() {
        fetch('/notifications/count/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Сетевая ошибка');
                }
                return response.json();
            })
            .then(data => {
                if (data && data.count !== undefined) {
                    updateNotificationCount(data.count);
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке количества уведомлений:', error);
            });
    }
    
    // Получает CSRF-токен из cookie
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Обработчики событий
    notificationButton.addEventListener('click', function(event) {
        event.stopPropagation();
        if (notificationDropdown.classList.contains('hidden')) {
            showDropdown();
        } else {
            hideDropdown();
        }
    });
    
    // Закрытие при клике вне
    document.addEventListener('click', function(event) {
        if (!notificationDropdown.contains(event.target) && !notificationButton.contains(event.target)) {
            hideDropdown();
        }
    });
    
    // Пересчитывать позицию при изменении размера окна
    window.addEventListener('resize', function() {
        if (!notificationDropdown.classList.contains('hidden')) {
            positionDropdown();
        }
    });
    
    // Отметка всех как прочитанных
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function(event) {
            event.preventDefault();
            markAllAsRead();
        });
    }
    
    // Загружаем начальное количество непрочитанных уведомлений
    loadNotificationCount();
    
    // Периодическое обновление счетчика уведомлений (каждые 60 секунд)
    setInterval(loadNotificationCount, 60000);
});