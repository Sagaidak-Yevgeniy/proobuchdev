/**
 * Система уведомлений для образовательной платформы
 */

// Создаем контейнер для уведомлений, если его еще нет
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1000';
        container.style.maxWidth = '350px';
        document.body.appendChild(container);
    }
});

/**
 * Показывает уведомление заданного типа
 * @param {string} message - Сообщение для отображения
 * @param {string} type - Тип уведомления (success, error, info, warning)
 * @param {number} duration - Длительность отображения в миллисекундах
 */
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notification-container');
    
    // Определяем классы в зависимости от типа уведомления
    let typeClasses = '';
    let icon = '';
    
    switch (type) {
        case 'success':
            typeClasses = 'bg-green-100 border-green-500 text-green-800';
            icon = '<i class="fas fa-check-circle text-green-600 mr-2"></i>';
            break;
        case 'error':
            typeClasses = 'bg-red-100 border-red-500 text-red-800';
            icon = '<i class="fas fa-exclamation-circle text-red-600 mr-2"></i>';
            break;
        case 'warning':
            typeClasses = 'bg-yellow-100 border-yellow-500 text-yellow-800';
            icon = '<i class="fas fa-exclamation-triangle text-yellow-600 mr-2"></i>';
            break;
        case 'info':
        default:
            typeClasses = 'bg-blue-100 border-blue-500 text-blue-800';
            icon = '<i class="fas fa-info-circle text-blue-600 mr-2"></i>';
            break;
    }
    
    // Создаем HTML элемент уведомления
    const notification = document.createElement('div');
    notification.className = `notification ${typeClasses} shadow-md rounded-md px-4 py-3 mb-4 border-l-4 transform transition-all duration-300`;
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(40px)';
    notification.style.overflow = 'hidden';
    notification.style.maxHeight = '0';
    
    // Формируем содержимое уведомления
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                ${icon}
                <span>${message}</span>
            </div>
            <button class="close-notification text-gray-600 hover:text-gray-800 ml-2 focus:outline-none">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Добавляем уведомление в контейнер
    container.prepend(notification);
    
    // Анимируем появление
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
        notification.style.maxHeight = '100px';
    }, 10);
    
    // Добавляем обработчик клика на кнопку закрытия
    notification.querySelector('.close-notification').addEventListener('click', function() {
        closeNotification(notification);
    });
    
    // Автоматическое закрытие через заданное время
    if (duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, duration);
    }
    
    // Возвращаем элемент уведомления (может быть полезно для управления им извне)
    return notification;
}

/**
 * Закрывает уведомление с анимацией
 * @param {HTMLElement} notification - Элемент уведомления
 */
function closeNotification(notification) {
    // Анимация исчезновения
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(40px)';
    notification.style.maxHeight = '0';
    
    // Удаляем элемент после завершения анимации
    setTimeout(() => {
        notification.remove();
    }, 300);
}

// Экспортируем функцию для использования в других модулях
window.showNotification = showNotification;