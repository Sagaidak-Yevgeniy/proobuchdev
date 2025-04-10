document.addEventListener('DOMContentLoaded', function() {
    const timerElement = document.getElementById('olympiad-timer');
    if (!timerElement) return;
    
    const hoursElement = document.getElementById('hours');
    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    const timeWarning = document.getElementById('time-warning');
    const warningText = document.getElementById('warning-text');
    const olympiadId = document.getElementById('olympiad-id').value;
    
    // Получаем оставшееся время в минутах из скрытого поля
    let remainingMinutes = parseInt(document.getElementById('remaining-minutes').value);
    let remainingSeconds = remainingMinutes * 60;
    let totalSeconds = remainingSeconds;
    let lastUpdateTime = Date.now();
    
    function updateTimer() {
        // Вычисляем реальное затраченное время с последнего обновления
        const now = Date.now();
        const elapsedSeconds = Math.floor((now - lastUpdateTime) / 1000);
        lastUpdateTime = now;
        
        // Обновляем оставшееся время
        remainingSeconds = Math.max(0, remainingSeconds - elapsedSeconds);
        
        // Вычисляем часы, минуты и секунды
        const hours = Math.floor(remainingSeconds / 3600);
        const minutes = Math.floor((remainingSeconds % 3600) / 60);
        const seconds = remainingSeconds % 60;
        
        // Обновляем отображение
        hoursElement.textContent = hours.toString().padStart(2, '0');
        minutesElement.textContent = minutes.toString().padStart(2, '0');
        secondsElement.textContent = seconds.toString().padStart(2, '0');
        
        // Обновляем прогресс-бар
        const progress = Math.min(100, 100 - (remainingSeconds / totalSeconds * 100));
        progressBar.style.width = `${progress}%`;
        progressPercentage.textContent = `${Math.round(progress)}%`;
        
        // Показываем предупреждение, если осталось мало времени
        if (remainingSeconds <= 300 && remainingSeconds > 0) { // Меньше 5 минут
            timeWarning.classList.remove('hidden');
            
            // Разные сообщения в зависимости от оставшегося времени
            if (remainingSeconds <= 60) {
                warningText.textContent = 'Осталось меньше минуты до окончания!';
                timeWarning.classList.add('animate-pulse');
            } else {
                const mins = Math.ceil(remainingSeconds / 60);
                warningText.textContent = `Осталось меньше ${mins} минут до окончания!`;
            }
            
            // Изменяем цвет прогресс-бара при малом времени
            if (remainingSeconds <= 60) {
                progressBar.classList.remove('bg-blue-600', 'bg-yellow-500');
                progressBar.classList.add('bg-red-600');
            } else {
                progressBar.classList.remove('bg-blue-600', 'bg-red-600');
                progressBar.classList.add('bg-yellow-500');
            }
        } else if (remainingSeconds > 300) {
            timeWarning.classList.add('hidden');
            progressBar.classList.remove('bg-yellow-500', 'bg-red-600');
            progressBar.classList.add('bg-blue-600');
        }
        
        // Если время закончилось
        if (remainingSeconds <= 0) {
            clearInterval(timerInterval);
            
            // Показываем итоговое сообщение
            timeWarning.classList.remove('hidden', 'bg-red-100', 'text-red-700');
            timeWarning.classList.add('bg-yellow-100', 'text-yellow-700');
            warningText.textContent = 'Время олимпиады закончилось! Перенаправление...';
            
            // Форсировано завершаем олимпиаду
            setTimeout(function() {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/olympiads/${olympiadId}/finish/`;
                
                // Добавляем CSRF токен
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.appendChild(csrfInput);
                
                document.body.appendChild(form);
                form.submit();
            }, 3000);
        }
    }
    
    // Запускаем таймер и обновляем каждую секунду
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
    
    // Периодически обновляем данные о прогрессе с сервера
    function updateProgress() {
        fetch(`/olympiads/${olympiadId}/update_progress/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Обновляем оставшееся время, если оно изменилось
                const serverMinutes = data.time_left_minutes;
                const currentMinutes = Math.ceil(remainingSeconds / 60);
                
                if (Math.abs(serverMinutes - currentMinutes) > 1) {
                    remainingSeconds = serverMinutes * 60;
                    totalSeconds = Math.max(totalSeconds, remainingSeconds);
                    updateTimer();
                }
                
                // Обновляем статусы задач, если необходимо
                // Дополнительная логика для обновления индикаторов задач
                const taskStatuses = data.task_statuses;
                if (taskStatuses) {
                    // Здесь можно обновить статусы заданий, если нужно
                }
            } else if (data.status === 'error' && data.message === 'Олимпиада уже завершена') {
                // Если олимпиада уже завершена, перенаправляем на страницу результатов
                window.location.href = `/olympiads/${olympiadId}/results/`;
            }
        })
        .catch(error => {
            console.error('Ошибка при обновлении прогресса:', error);
        });
    }
    
    // Обновляем прогресс каждую минуту
    const progressInterval = setInterval(updateProgress, 60000);
    
    // Очищаем интервалы при уходе со страницы
    window.addEventListener('beforeunload', function() {
        clearInterval(timerInterval);
        clearInterval(progressInterval);
    });
});