/**
 * Модуль для обеспечения CSRF-защиты во всех AJAX-запросах и формах
 * Решает проблемы с токенами CSRF в среде Replit
 */

// Функция для получения CSRF-токена из cookie
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

// Глобальный CSRF-токен
const csrftoken = getCookie('csrftoken');

// Функция для обновления CSRF-токенов в формах
function updateCsrfTokens() {
    console.log('Updating CSRF tokens in all forms');
    const csrfInputs = document.querySelectorAll('input[name="csrfmiddlewaretoken"]');
    const token = getCookie('csrftoken');
    
    if (token) {
        csrfInputs.forEach(input => {
            input.value = token;
        });
    } else {
        console.warn('No CSRF token found in cookies');
    }
}

// Добавляем CSRF-токены ко всем AJAX-запросам
function setupAjaxCsrf() {
    // Добавляем CSRF-токен ко всем AJAX-запросам
    document.addEventListener('DOMContentLoaded', function() {
        const token = getCookie('csrftoken');
        if (!token) {
            console.warn('CSRF token not found in cookies. AJAX requests may fail.');
            return;
        }

        // Перехватываем все fetch-запросы и добавляем CSRF-токен
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            // Для POST, PUT, DELETE запросов добавляем CSRF-токен
            if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
                if (!options.headers) {
                    options.headers = {};
                }
                
                // Преобразуем заголовки в формат, который можно модифицировать
                if (options.headers instanceof Headers) {
                    const newHeaders = {};
                    for (const [key, value] of options.headers.entries()) {
                        newHeaders[key] = value;
                    }
                    options.headers = newHeaders;
                }

                // Добавляем CSRF-токен, если он не был добавлен ранее
                if (!options.headers['X-CSRFToken']) {
                    options.headers['X-CSRFToken'] = token;
                }
            }
            return originalFetch(url, options);
        };
        
        // Отслеживаем все XMLHttpRequest запросы
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            const xhr = this;
            const originalSetRequestHeader = xhr.setRequestHeader;
            
            // Для POST, PUT, DELETE запросов добавляем CSRF-токен
            if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
                xhr.setRequestHeader = function(header, value) {
                    if (header.toLowerCase() === 'x-csrftoken') {
                        // Если заголовок уже задан, не переопределяем
                        originalSetRequestHeader.apply(this, arguments);
                    } else {
                        originalSetRequestHeader.apply(this, arguments);
                        // Добавляем CSRF токен только один раз
                        if (header.toLowerCase() === 'content-type') {
                            originalSetRequestHeader.call(this, 'X-CSRFToken', token);
                        }
                    }
                };
            }
            
            originalOpen.apply(this, arguments);
        };
    });
}

// Функция для добавления обработчиков отправки форм
function setupFormSubmitHandlers() {
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Не обрабатываем формы, у которых уже есть специальный обработчик
            // или формы с атрибутом data-no-csrf
            if (form.getAttribute('data-no-csrf') === 'true') {
                return;
            }
            
            form.addEventListener('submit', function(e) {
                // Обновляем токен перед отправкой
                const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
                const token = getCookie('csrftoken');
                
                if (token && tokenInput) {
                    tokenInput.value = token;
                } else if (token && !tokenInput && (form.method || 'GET').toUpperCase() === 'POST') {
                    // Если токена нет, но форма отправляется как POST, добавляем токен
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrfmiddlewaretoken';
                    input.value = token;
                    form.appendChild(input);
                }
            });
        });
    });
}

// Функция периодического обновления токенов в случае, если они меняются
function setupTokenRefresh() {
    // Обновляем токены каждые 5 минут на случай, если сессия обновится
    setInterval(updateCsrfTokens, 5 * 60 * 1000);
    
    // Также обновляем при фокусировке на странице после переключения с другой вкладки
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            updateCsrfTokens();
        }
    });
}

// Инициализация всех функций CSRF-защиты
function initCsrfProtection() {
    updateCsrfTokens();
    setupAjaxCsrf();
    setupFormSubmitHandlers();
    setupTokenRefresh();
    
    console.log('CSRF protection initialized');
}

// Запускаем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', initCsrfProtection);