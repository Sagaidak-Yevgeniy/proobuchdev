/**
 * Таймер обратного отсчета для олимпиад с ограничением времени
 */
document.addEventListener('DOMContentLoaded', function() {
    const timerContainer = document.getElementById('olympiad-timer');
    
    if (!timerContainer) return;
    
    const endTimeStr = timerContainer.dataset.endTime;
    const timeLimit = parseInt(timerContainer.dataset.timeLimit || '0', 10);
    const startTimeStr = timerContainer.dataset.startTime;
    
    // Определяем время окончания
    let endTime;
    
    if (timeLimit > 0 && startTimeStr) {
        // Если есть ограничение по времени, расчитываем из времени начала + лимит
        const startTime = new Date(startTimeStr);
        endTime = new Date(startTime.getTime() + timeLimit * 60 * 1000);
    } else if (endTimeStr) {
        // Иначе используем время окончания олимпиады
        endTime = new Date(endTimeStr);
    } else {
        return; // Нет данных для таймера
    }
    
    const timerDisplay = document.getElementById('timer-display');
    const progressBar = document.getElementById('timer-progress');
    const timerAlert = document.getElementById('timer-alert');
    
    // Обновляем таймер каждую секунду
    function updateTimer() {
        const now = new Date();
        const timeLeft = endTime - now;
        
        if (timeLeft <= 0) {
            // Время вышло
            clearInterval(timerInterval);
            timerDisplay.innerHTML = '00:00:00';
            timerAlert.classList.remove('hidden');
            progressBar.style.width = '0%';
            
            // Перенаправляем на страницу результатов через 5 секунд
            setTimeout(() => {
                const olympiadId = timerContainer.dataset.olympiadId;
                window.location.href = `/olympiads/results/${olympiadId}/`;
            }, 5000);
            
            return;
        }
        
        // Рассчитываем часы, минуты и секунды
        const hours = Math.floor(timeLeft / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
        
        // Форматируем и отображаем время
        timerDisplay.innerHTML = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        // Обновляем прогресс-бар, если задан лимит времени
        if (timeLimit > 0 && startTimeStr) {
            const startTime = new Date(startTimeStr);
            const totalDuration = endTime - startTime;
            const elapsed = now - startTime;
            const percentLeft = 100 - (elapsed / totalDuration * 100);
            progressBar.style.width = `${Math.max(0, percentLeft)}%`;
            
            // Меняем цвет индикатора, если осталось мало времени
            if (percentLeft < 20) {
                progressBar.classList.remove('bg-blue-600');
                progressBar.classList.add('bg-red-600');
            } else if (percentLeft < 50) {
                progressBar.classList.remove('bg-blue-600');
                progressBar.classList.add('bg-yellow-500');
            }
        }
        
        // Предупреждаем, если осталось 5 минут
        if (timeLeft <= 5 * 60 * 1000 && !timerAlert.classList.contains('animate-pulse')) {
            timerAlert.classList.remove('hidden');
            timerAlert.classList.add('animate-pulse');
        }
    }
    
    // Инициализируем таймер
    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
    
    // Отправляем данные о времени на сервер каждую минуту
    // для обновления прогресса участника
    setInterval(() => {
        const olympiadId = timerContainer.dataset.olympiadId;
        fetch(`/olympiads/update_progress/${olympiadId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).catch(error => console.error('Failed to update progress:', error));
    }, 60 * 1000);
});