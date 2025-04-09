// Улучшенная функция для обеспечения правильной работы CSRF в среде Replit
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Получаем CSRF-токен из куки
     * @param {string} name - Имя куки
     * @returns {string} - Значение куки или null, если не найдено
     */
    function getCookie(name) {
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
    
    // Функция для обновления CSRF токена
    function updateCSRFToken() {
        // Получаем актуальный токен из куки или из формы
        const newToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (newToken) {
            // Обновляем все существующие скрытые поля CSRF токенов в формах
            document.querySelectorAll('input[name="csrfmiddlewaretoken"]').forEach(input => {
                input.value = newToken;
            });
            
            return newToken;
        } else {
            console.warn('CSRF токен не найден. Это может вызвать проблемы при отправке форм.');
            return null;
        }
    }
    
    // Получаем начальный CSRF токен
    let csrftoken = updateCSRFToken();
    
    if (csrftoken) {
        // Переопределяем метод отправки XMLHttpRequest для автоматического добавления CSRF-токена
        const xhrOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function() {
            const result = xhrOpen.apply(this, arguments);
            
            // Получаем актуальный токен перед каждым запросом
            const currentToken = updateCSRFToken() || csrftoken;
            
            this.setRequestHeader('X-CSRFToken', currentToken);
            return result;
        };
        
        // Обработка существующих форм
        function setupForms() {
            document.querySelectorAll('form').forEach(form => {
                if (form.method.toLowerCase() === 'post' && !form.hasAttribute('data-csrf-handled')) {
                    // Помечаем форму как обработанную
                    form.setAttribute('data-csrf-handled', 'true');
                    
                    // Проверяем, есть ли уже поле csrfmiddlewaretoken
                    let csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
                    
                    if (!csrfInput) {
                        // Если нет, создаем новое поле
                        csrfInput = document.createElement('input');
                        csrfInput.type = 'hidden';
                        csrfInput.name = 'csrfmiddlewaretoken';
                        form.appendChild(csrfInput);
                    }
                    
                    // Добавляем CSRF-токен в данные формы при отправке
                    form.addEventListener('submit', function(e) {
                        // Обновляем токен перед отправкой
                        const currentToken = updateCSRFToken() || csrftoken;
                        
                        // Обновляем значение поля
                        csrfInput.value = currentToken;
                    });
                }
            });
        }
        
        // Настраиваем существующие формы при загрузке страницы
        setupForms();
        
        // Настраиваем MutationObserver для обработки динамически добавленных форм
        const observer = new MutationObserver(function(mutations) {
            let shouldCheckForms = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Проверяем, были ли добавлены новые формы или элементы, содержащие формы
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeName === 'FORM' || 
                            (node.nodeType === 1 && node.querySelector('form'))) {
                            shouldCheckForms = true;
                        }
                    });
                }
            });
            
            // Если были добавлены новые формы, настраиваем их
            if (shouldCheckForms) {
                setupForms();
            }
        });
        
        // Запускаем наблюдение за изменениями DOM
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // Периодически обновляем CSRF токен для долго живущих страниц
        setInterval(function() {
            csrftoken = updateCSRFToken() || csrftoken;
        }, 300000); // Обновление каждые 5 минут
    }
});