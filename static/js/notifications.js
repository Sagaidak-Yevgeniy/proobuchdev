/**
 * Модуль для управления уведомлениями
 */
class NotificationManager {
    /**
     * Инициализирует менеджер уведомлений
     * @param {Object} options - настройки уведомлений
     */
    constructor(options = {}) {
        this.options = {
            position: options.position || 'top-right',
            duration: options.duration || 5000,
            maxNotifications: options.maxNotifications || 5,
            animations: options.animations !== false,
            sounds: options.sounds !== false,
            container: options.container || null
        };
        
        this.notifications = [];
        this.container = null;
        
        // Создаем контейнер для уведомлений
        this.createContainer();
        
        // Загружаем звуки
        this.sounds = {
            success: new Audio('/static/sounds/success.mp3'),
            error: new Audio('/static/sounds/error.mp3'),
            warning: new Audio('/static/sounds/warning.mp3'),
            info: new Audio('/static/sounds/info.mp3')
        };
        
        // Устанавливаем обработчик для скрытия уведомлений при клике вне них
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notification') && !e.target.closest('.notification-container')) {
                this.hideAll();
            }
        });
    }
    
    /**
     * Создает контейнер для уведомлений
     */
    createContainer() {
        // Если контейнер уже существует, используем его
        if (this.options.container) {
            this.container = document.querySelector(this.options.container);
            if (this.container) {
                this.container.classList.add('notification-container');
                return;
            }
        }
        
        // Создаем новый контейнер
        this.container = document.createElement('div');
        this.container.className = `notification-container ${this.options.position}`;
        document.body.appendChild(this.container);
        
        // Добавляем стили
        this.addStyles();
    }
    
    /**
     * Добавляет стили для уведомлений
     */
    addStyles() {
        // Проверяем, не добавлены ли уже стили
        if (document.getElementById('notification-styles')) {
            return;
        }
        
        // Создаем элемент для стилей
        const styleEl = document.createElement('style');
        styleEl.id = 'notification-styles';
        
        // Определяем стили
        styleEl.textContent = `
            .notification-container {
                position: fixed;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                max-width: 100%;
                max-height: 100vh;
                overflow-y: auto;
                padding: 10px;
                pointer-events: none;
            }
            
            .notification-container.top-right {
                top: 0;
                right: 0;
                align-items: flex-end;
            }
            
            .notification-container.top-left {
                top: 0;
                left: 0;
                align-items: flex-start;
            }
            
            .notification-container.bottom-right {
                bottom: 0;
                right: 0;
                align-items: flex-end;
                flex-direction: column-reverse;
            }
            
            .notification-container.bottom-left {
                bottom: 0;
                left: 0;
                align-items: flex-start;
                flex-direction: column-reverse;
            }
            
            .notification {
                background-color: white;
                color: #333;
                border-radius: 4px;
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16);
                margin: 5px 0;
                padding: 15px;
                max-width: 350px;
                pointer-events: auto;
                display: flex;
                align-items: flex-start;
                transform-origin: center right;
                animation: notification-in 0.3s ease forwards;
                position: relative;
                overflow: hidden;
            }
            
            .notification.is-hiding {
                animation: notification-out 0.3s ease forwards;
            }
            
            .notification.success {
                border-left: 4px solid #48bb78;
            }
            
            .notification.error {
                border-left: 4px solid #f56565;
            }
            
            .notification.warning {
                border-left: 4px solid #ed8936;
            }
            
            .notification.info {
                border-left: 4px solid #4299e1;
            }
            
            .notification-icon {
                margin-right: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 20px;
                height: 20px;
                flex-shrink: 0;
            }
            
            .notification-content {
                flex-grow: 1;
            }
            
            .notification-title {
                font-weight: bold;
                margin-bottom: 5px;
                font-size: 1rem;
            }
            
            .notification-message {
                font-size: 0.875rem;
                line-height: 1.4;
            }
            
            .notification-close {
                background: transparent;
                border: none;
                color: #a0aec0;
                cursor: pointer;
                font-size: 0.875rem;
                padding: 5px;
                margin-left: 10px;
                margin-top: -5px;
                margin-right: -5px;
                transition: color 0.2s;
            }
            
            .notification-close:hover {
                color: #4a5568;
            }
            
            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                width: 100%;
                background-color: rgba(0, 0, 0, 0.1);
            }
            
            .notification-progress-bar {
                height: 100%;
                width: 100%;
                transform-origin: left;
                animation: progress-bar 5s linear forwards;
            }
            
            .success .notification-progress-bar {
                background-color: #48bb78;
            }
            
            .error .notification-progress-bar {
                background-color: #f56565;
            }
            
            .warning .notification-progress-bar {
                background-color: #ed8936;
            }
            
            .info .notification-progress-bar {
                background-color: #4299e1;
            }
            
            .dark-mode .notification {
                background-color: #2d3748;
                color: #e2e8f0;
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
            }
            
            .dark-mode .notification-close {
                color: #a0aec0;
            }
            
            .dark-mode .notification-close:hover {
                color: #e2e8f0;
            }
            
            .dark-mode .notification-progress {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            @keyframes notification-in {
                0% {
                    opacity: 0;
                    transform: translateX(40px);
                }
                100% {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes notification-out {
                0% {
                    opacity: 1;
                    transform: translateX(0);
                }
                100% {
                    opacity: 0;
                    transform: translateX(40px);
                }
            }
            
            @keyframes progress-bar {
                0% {
                    width: 100%;
                }
                100% {
                    width: 0%;
                }
            }
        `;
        
        // Добавляем стили на страницу
        document.head.appendChild(styleEl);
    }
    
    /**
     * Создает новое уведомление
     * @param {string} type - тип уведомления (success, error, warning, info)
     * @param {string} message - текст уведомления
     * @param {Object} options - дополнительные настройки
     */
    create(type, message, options = {}) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        // Определяем иконку в зависимости от типа
        let iconSvg;
        switch (type) {
            case 'success':
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#48bb78" width="20" height="20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>`;
                break;
            case 'error':
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#f56565" width="20" height="20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>`;
                break;
            case 'warning':
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#ed8936" width="20" height="20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>`;
                break;
            case 'info':
                iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#4299e1" width="20" height="20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>`;
                break;
        }
        
        // Формируем содержимое уведомления
        notification.innerHTML = `
            <div class="notification-icon">${iconSvg}</div>
            <div class="notification-content">
                ${options.title ? `<div class="notification-title">${options.title}</div>` : ''}
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">&times;</button>
            ${this.options.animations ? `
                <div class="notification-progress">
                    <div class="notification-progress-bar" style="animation-duration: ${options.duration || this.options.duration}ms"></div>
                </div>
            ` : ''}
        `;
        
        // Добавляем обработчик для кнопки закрытия
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            this.hide(notification);
        });
        
        // Добавляем уведомление в контейнер
        this.container.appendChild(notification);
        
        // Воспроизводим звук, если включено
        if (this.options.sounds && this.sounds[type]) {
            this.sounds[type].play().catch(() => {
                // Игнорируем ошибки воспроизведения звука
                // (часто возникают из-за политики браузеров, требующей взаимодействия пользователя)
            });
        }
        
        // Если уведомлений больше максимального количества, удаляем самое старое
        if (this.notifications.length >= this.options.maxNotifications) {
            this.hide(this.notifications[0].element);
        }
        
        // Добавляем уведомление в список
        const notificationObj = {
            element: notification,
            type,
            message,
            timeoutId: null
        };
        
        this.notifications.push(notificationObj);
        
        // Устанавливаем таймер для автоматического скрытия
        if (options.duration !== 0) {
            notificationObj.timeoutId = setTimeout(() => {
                this.hide(notification);
            }, options.duration || this.options.duration);
        }
        
        // Возвращаем объект уведомления
        return notificationObj;
    }
    
    /**
     * Скрывает уведомление
     * @param {HTMLElement} notification - элемент уведомления
     */
    hide(notification) {
        // Находим индекс уведомления в массиве
        const index = this.notifications.findIndex(n => n.element === notification);
        
        if (index !== -1) {
            // Получаем объект уведомления
            const notificationObj = this.notifications[index];
            
            // Очищаем таймер, если он существует
            if (notificationObj.timeoutId) {
                clearTimeout(notificationObj.timeoutId);
            }
            
            // Удаляем уведомление из массива
            this.notifications.splice(index, 1);
        }
        
        // Добавляем класс для анимации скрытия
        if (this.options.animations) {
            notification.classList.add('is-hiding');
            
            // Удаляем уведомление после завершения анимации
            notification.addEventListener('animationend', () => {
                notification.remove();
            });
        } else {
            // Если анимации отключены, просто удаляем уведомление
            notification.remove();
        }
    }
    
    /**
     * Скрывает все уведомления
     */
    hideAll() {
        // Копируем массив, чтобы избежать проблем при итерации
        const notifications = [...this.notifications];
        
        // Скрываем каждое уведомление
        notifications.forEach(notification => {
            this.hide(notification.element);
        });
    }
    
    /**
     * Создает уведомление типа "success"
     * @param {string} message - текст уведомления
     * @param {Object} options - дополнительные настройки
     */
    success(message, options = {}) {
        return this.create('success', message, options);
    }
    
    /**
     * Создает уведомление типа "error"
     * @param {string} message - текст уведомления
     * @param {Object} options - дополнительные настройки
     */
    error(message, options = {}) {
        return this.create('error', message, options);
    }
    
    /**
     * Создает уведомление типа "warning"
     * @param {string} message - текст уведомления
     * @param {Object} options - дополнительные настройки
     */
    warning(message, options = {}) {
        return this.create('warning', message, options);
    }
    
    /**
     * Создает уведомление типа "info"
     * @param {string} message - текст уведомления
     * @param {Object} options - дополнительные настройки
     */
    info(message, options = {}) {
        return this.create('info', message, options);
    }
}

// Создаем глобальный экземпляр менеджера уведомлений
const notifications = new NotificationManager();

// Заменяем стандартные функции алертов
function showNotification(message, type = 'info', options = {}) {
    return notifications[type](message, options);
}

// Функция для отображения сообщений об ошибках из форм
function showFormErrors(form, errors) {
    if (typeof errors === 'string') {
        showNotification(errors, 'error');
        return;
    }
    
    // Если errors - объект с полями
    for (const field in errors) {
        const errorMessages = errors[field];
        const fieldElement = form.querySelector(`[name="${field}"]`);
        
        if (fieldElement) {
            // Добавляем класс ошибки к полю
            fieldElement.classList.add('is-invalid');
            
            // Создаем или обновляем сообщение об ошибке
            let errorContainer = fieldElement.nextElementSibling;
            if (!errorContainer || !errorContainer.classList.contains('invalid-feedback')) {
                errorContainer = document.createElement('div');
                errorContainer.className = 'invalid-feedback';
                fieldElement.parentNode.insertBefore(errorContainer, fieldElement.nextSibling);
            }
            
            // Заполняем сообщение об ошибке
            errorContainer.textContent = Array.isArray(errorMessages) ? errorMessages[0] : errorMessages;
            errorContainer.style.display = 'block';
            
            // Устанавливаем обработчик для сброса ошибки при изменении поля
            fieldElement.addEventListener('input', function onInput() {
                fieldElement.classList.remove('is-invalid');
                errorContainer.style.display = 'none';
                fieldElement.removeEventListener('input', onInput);
            });
        } else {
            // Если поле не найдено, показываем общее уведомление об ошибке
            const errorMessage = Array.isArray(errorMessages) ? errorMessages[0] : errorMessages;
            showNotification(`${field}: ${errorMessage}`, 'error');
        }
    }
}

// Экспортируем функции и объекты
window.notifications = notifications;
window.showNotification = showNotification;
window.showFormErrors = showFormErrors;