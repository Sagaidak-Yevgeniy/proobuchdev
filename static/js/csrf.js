// Функция для обеспечения правильной работы CSRF в среде Replit
document.addEventListener('DOMContentLoaded', function() {
    // Получаем CSRF-токен из куки
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
    
    const csrftoken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    if (csrftoken) {
        // Устанавливаем CSRF-токен для всех Ajax-запросов
        const xhrOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function() {
            const result = xhrOpen.apply(this, arguments);
            this.setRequestHeader('X-CSRFToken', csrftoken);
            return result;
        };
        
        // Обработка отправки всех форм
        document.querySelectorAll('form').forEach(form => {
            if (form.method.toLowerCase() === 'post') {
                // Проверяем, есть ли уже поле csrfmiddlewaretoken
                if (!form.querySelector('input[name="csrfmiddlewaretoken"]')) {
                    const csrfField = document.createElement('input');
                    csrfField.type = 'hidden';
                    csrfField.name = 'csrfmiddlewaretoken';
                    csrfField.value = csrftoken;
                    form.appendChild(csrfField);
                }
                
                // Добавляем CSRF-токен в данные формы при отправке
                form.addEventListener('submit', function(e) {
                    const formData = new FormData(form);
                    if (!formData.has('csrfmiddlewaretoken')) {
                        formData.append('csrfmiddlewaretoken', csrftoken);
                    }
                });
            }
        });
    } else {
        console.warn('CSRF токен не найден. Это может вызвать проблемы при отправке форм.');
    }
});