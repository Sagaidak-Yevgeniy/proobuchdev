/**
 * Система уведомлений - JavaScript
 * 
 * Обеспечивает интерактивность работы с уведомлениями:
 * - Загрузка уведомлений через AJAX
 * - Отображение счетчика непрочитанных уведомлений
 * - Отметка уведомлений как прочитанных
 * - Удаление уведомлений
 */

document.addEventListener('DOMContentLoaded', function() {
    // Элементы интерфейса
    const notificationButton = document.getElementById('notification-button');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const notificationList = document.getElementById('notification-list');
    const notificationCount = document.querySelector('.notification-count');
    const notificationNoItems = document.getElementById('notification-no-items');
    const markAllAsReadButton = document.getElementById('mark-all-as-read');
    
    // Состояние системы уведомлений
    let isDropdownOpen = false;
    let notifications = [];
    let unreadCount = 0;
    
    // Загрузка уведомлений при первой загрузке страницы
    loadNotifications();
    
    // Загрузка уведомлений каждые 30 секунд
    setInterval(loadNotifications, 30000);
    
    // Обработка клика по кнопке уведомлений
    if (notificationButton) {
        notificationButton.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            toggleNotificationDropdown();
        });
    }
    
    // Обработка клика по кнопке "Отметить все как прочитанные"
    if (markAllAsReadButton) {
        markAllAsReadButton.addEventListener('click', function(event) {
            event.preventDefault();
            markAllAsRead();
        });
    }
    
    // Закрытие выпадающего списка при клике вне его
    document.addEventListener('click', function(event) {
        if (isDropdownOpen && !notificationDropdown.contains(event.target) && event.target !== notificationButton) {
            closeNotificationDropdown();
        }
    });
    
    /**
     * Загружает уведомления с сервера через AJAX
     */
    function loadNotifications() {
        fetch('/notifications/count/')
            .then(response => response.json())
            .then(data => {
                updateNotificationCount(data.count);
            })
            .catch(error => console.error('Ошибка при загрузке количества уведомлений:', error));
    }
    
    /**
     * Загружает список уведомлений для отображения в выпадающем меню
     */
    function loadNotificationsList() {
        fetch('/notifications/list/?format=json')
            .then(response => response.json())
            .then(data => {
                notifications = data.notifications;
                unreadCount = data.unread_count;
                renderNotifications();
                updateNotificationCount(unreadCount);
            })
            .catch(error => console.error('Ошибка при загрузке списка уведомлений:', error));
    }
    
    /**
     * Обновляет счетчик непрочитанных уведомлений
     * @param {number} count - Количество непрочитанных уведомлений
     */
    function updateNotificationCount(count) {
        if (count > 0) {
            notificationCount.textContent = count > 99 ? '99+' : count;
            notificationCount.classList.remove('hidden');
        } else {
            notificationCount.classList.add('hidden');
        }
        unreadCount = count;
    }
    
    /**
     * Отображает уведомления в выпадающем списке
     */
    function renderNotifications() {
        // Очищаем список
        notificationList.innerHTML = '';
        
        if (notifications.length === 0) {
            // Если уведомлений нет, показываем сообщение
            notificationNoItems.classList.remove('hidden');
            return;
        }
        
        // Скрываем сообщение "Нет уведомлений"
        notificationNoItems.classList.add('hidden');
        
        // Отображаем уведомления
        notifications.forEach(notification => {
            const listItem = document.createElement('li');
            listItem.className = `notification-item ${!notification.is_read ? 'bg-blue-50 dark:bg-blue-900/20' : ''} hover:bg-gray-50 dark:hover:bg-gray-700 p-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0`;
            listItem.dataset.id = notification.id;
            
            // Выбираем иконку в зависимости от типа уведомления
            let icon = '';
            switch(notification.notification_type) {
                case 'info':
                    icon = '<svg class="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                    break;
                case 'success':
                    icon = '<svg class="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                    break;
                case 'warning':
                    icon = '<svg class="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>';
                    break;
                case 'error':
                    icon = '<svg class="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>';
                    break;
                case 'achievement':
                    icon = '<svg class="h-5 w-5 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>';
                    break;
                default:
                    icon = '<svg class="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>';
            }
            
            // Форматируем дату
            const date = new Date(notification.created_at);
            const formattedDate = `${date.toLocaleDateString('ru-RU', {day: '2-digit', month: '2-digit', year: 'numeric'})} ${date.toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}`;
            
            // Создаем содержимое элемента
            let content = `
                <div class="flex items-start">
                    <div class="flex-shrink-0 mr-3">
                        ${icon}
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between">
                            <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                ${notification.url ? `<a href="${notification.url}" class="hover:underline">${notification.title}</a>` : notification.title}
                                ${notification.is_high_priority ? '<span class="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">!</span>' : ''}
                            </p>
                            <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2">${formattedDate}</span>
                        </div>
                        <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">${notification.message}</p>
                        
                        <div class="mt-2 flex justify-end space-x-3">
                            ${!notification.is_read ? `<button class="mark-read-button text-xs text-blue-600 dark:text-blue-400 hover:underline" data-id="${notification.id}">Прочитано</button>` : ''}
                            <button class="delete-button text-xs text-red-600 dark:text-red-400 hover:underline" data-id="${notification.id}">Удалить</button>
                        </div>
                    </div>
                </div>
            `;
            
            listItem.innerHTML = content;
            notificationList.appendChild(listItem);
        });
        
        // Добавляем обработчики для кнопок "Прочитано" и "Удалить"
        document.querySelectorAll('.mark-read-button').forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const id = this.dataset.id;
                markAsRead(id);
            });
        });
        
        document.querySelectorAll('.delete-button').forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const id = this.dataset.id;
                deleteNotification(id);
            });
        });
    }
    
    /**
     * Отмечает уведомление как прочитанное
     * @param {number} id - ID уведомления
     */
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
                // Обновляем счетчик
                updateNotificationCount(data.unread_count);
                
                // Обновляем внешний вид уведомления в списке
                const listItem = notificationList.querySelector(`[data-id="${id}"]`);
                if (listItem) {
                    listItem.classList.remove('bg-blue-50', 'dark:bg-blue-900/20');
                    const markAsReadButton = listItem.querySelector('.mark-read-button');
                    if (markAsReadButton) {
                        markAsReadButton.remove();
                    }
                }
                
                // Обновляем локальный массив уведомлений
                notifications = notifications.map(notification => {
                    if (notification.id == id) {
                        notification.is_read = true;
                    }
                    return notification;
                });
            }
        })
        .catch(error => console.error('Ошибка при отметке уведомления как прочитанного:', error));
    }
    
    /**
     * Отмечает все уведомления как прочитанные
     */
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
                // Обновляем счетчик
                updateNotificationCount(0);
                
                // Обновляем внешний вид всех уведомлений в списке
                notificationList.querySelectorAll('.notification-item').forEach(item => {
                    item.classList.remove('bg-blue-50', 'dark:bg-blue-900/20');
                    const markAsReadButton = item.querySelector('.mark-read-button');
                    if (markAsReadButton) {
                        markAsReadButton.remove();
                    }
                });
                
                // Обновляем локальный массив уведомлений
                notifications = notifications.map(notification => {
                    notification.is_read = true;
                    return notification;
                });
            }
        })
        .catch(error => console.error('Ошибка при отметке всех уведомлений как прочитанных:', error));
    }
    
    /**
     * Удаляет уведомление
     * @param {number} id - ID уведомления
     */
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
                // Обновляем счетчик
                updateNotificationCount(data.unread_count);
                
                // Удаляем уведомление из списка
                const listItem = notificationList.querySelector(`[data-id="${id}"]`);
                if (listItem) {
                    listItem.remove();
                }
                
                // Обновляем локальный массив уведомлений
                notifications = notifications.filter(notification => notification.id != id);
                
                // Если все уведомления удалены, показываем сообщение "Нет уведомлений"
                if (notifications.length === 0) {
                    notificationNoItems.classList.remove('hidden');
                }
            }
        })
        .catch(error => console.error('Ошибка при удалении уведомления:', error));
    }
    
    /**
     * Переключает видимость выпадающего списка уведомлений
     */
    function toggleNotificationDropdown() {
        if (isDropdownOpen) {
            closeNotificationDropdown();
        } else {
            openNotificationDropdown();
        }
    }
    
    /**
     * Открывает выпадающий список уведомлений
     */
    function openNotificationDropdown() {
        notificationDropdown.classList.remove('hidden');
        isDropdownOpen = true;
        
        // Загружаем список уведомлений при открытии
        loadNotificationsList();
    }
    
    /**
     * Закрывает выпадающий список уведомлений
     */
    function closeNotificationDropdown() {
        notificationDropdown.classList.add('hidden');
        isDropdownOpen = false;
    }
    
    /**
     * Получает CSRF-токен из cookie
     * @returns {string} CSRF-токен
     */
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
});