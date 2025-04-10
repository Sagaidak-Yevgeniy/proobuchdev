/**
 * Модуль для управления таймером олимпиады
 */
class OlympiadTimer {
    /**
     * Инициализирует таймер олимпиады
     * @param {Date} startDate - дата и время начала олимпиады
     * @param {Date} endDate - дата и время окончания олимпиады
     * @param {Object} elements - объект с DOM-элементами таймера
     * @param {Function} onTimeUpdate - функция обратного вызова при обновлении времени
     * @param {Function} onComplete - функция обратного вызова при завершении олимпиады
     */
    constructor(startDate, endDate, elements, onTimeUpdate, onComplete) {
        this.startDate = startDate;
        this.endDate = endDate;
        this.elements = elements;
        this.onTimeUpdate = onTimeUpdate || (() => {});
        this.onComplete = onComplete || (() => {});
        this.timerInterval = null;
        this.totalDuration = this.endDate - this.startDate;
        this.autoSaveInterval = null;
        this.autoSaveCallback = null;
    }

    /**
     * Запускает таймер
     */
    start() {
        this.updateTimer();
        this.timerInterval = setInterval(() => this.updateTimer(), 1000);
    }

    /**
     * Останавливает таймер
     */
    stop() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }

    /**
     * Обновляет таймер
     */
    updateTimer() {
        // Получаем текущее время
        const currentTime = new Date();
        
        // Вычисляем оставшееся время
        let timeRemaining, timerLabel, statusText, statusClass;
        
        if (currentTime < this.startDate) {
            // Олимпиада еще не началась
            timeRemaining = this.startDate - currentTime;
            timerLabel = "До начала олимпиады:";
            statusText = "Ожидание начала";
            statusClass = "text-yellow-600 dark:text-yellow-400";
        } else if (currentTime < this.endDate) {
            // Олимпиада идет
            timeRemaining = this.endDate - currentTime;
            timerLabel = "До окончания олимпиады:";
            statusText = "Активна";
            statusClass = "text-green-600 dark:text-green-400";
        } else {
            // Олимпиада завершена
            timeRemaining = 0;
            timerLabel = "Олимпиада завершена";
            statusText = "Завершена";
            statusClass = "text-red-600 dark:text-red-400";
            
            // Вызываем обратный вызов завершения, если олимпиада только что закончилась
            if (this.timerInterval) {
                this.onComplete();
                this.stop();
            }
        }
        
        // Обновляем статус
        if (this.elements.status) {
            this.elements.status.textContent = statusText;
            this.elements.status.className = '';
            this.elements.status.classList.add('font-bold', ...statusClass.split(' '));
        }
        
        // Обновляем текст таймера
        if (this.elements.timerLabel) {
            this.elements.timerLabel.textContent = timerLabel;
        }
        
        // Вычисляем дни, часы, минуты и секунды
        let days, hours, minutes, seconds;
        
        if (timeRemaining > 0) {
            days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
            hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
            seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
        } else {
            days = 0;
            hours = 0;
            minutes = 0;
            seconds = 0;
        }
        
        // Обновляем значения на странице
        if (this.elements.days) {
            this.elements.days.textContent = days.toString().padStart(2, '0');
        }
        
        if (this.elements.hours) {
            this.elements.hours.textContent = hours.toString().padStart(2, '0');
        }
        
        if (this.elements.minutes) {
            this.elements.minutes.textContent = minutes.toString().padStart(2, '0');
        }
        
        if (this.elements.seconds) {
            this.elements.seconds.textContent = seconds.toString().padStart(2, '0');
        }
        
        // Обновляем прогресс-бар
        if (this.elements.progressBar) {
            if (currentTime < this.startDate) {
                // До начала олимпиады
                this.elements.progressBar.style.width = '0%';
            } else if (currentTime >= this.endDate) {
                // После окончания олимпиады
                this.elements.progressBar.style.width = '100%';
            } else {
                // Во время олимпиады
                const elapsed = currentTime - this.startDate;
                const progressPercent = (elapsed / this.totalDuration) * 100;
                this.elements.progressBar.style.width = progressPercent + '%';
            }
        }
        
        // Вызываем обратный вызов обновления
        this.onTimeUpdate({
            timeRemaining,
            days,
            hours,
            minutes,
            seconds,
            status: statusText
        });
        
        // Если осталось меньше часа, меняем цвет таймера на красный
        if (this.elements.digits && timeRemaining > 0 && timeRemaining < 3600000) {
            this.elements.digits.classList.add('text-red-600', 'dark:text-red-400');
            this.elements.digits.classList.remove('text-blue-600', 'dark:text-blue-400');
            
            // Если меньше 5 минут, добавляем эффект пульсации
            if (timeRemaining < 300000) {
                this.elements.container.classList.add('animate-pulse');
            }
        }
    }
    
    /**
     * Включает автоматическое сохранение с заданным интервалом
     * @param {Function} callback - функция сохранения
     * @param {number} interval - интервал в миллисекундах между сохранениями
     */
    enableAutoSave(callback, interval = 60000) {
        if (!callback) return;
        
        this.autoSaveCallback = callback;
        
        // Останавливаем предыдущий интервал, если он был
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        // Запускаем новый интервал автосохранения
        this.autoSaveInterval = setInterval(() => {
            this.autoSaveCallback();
        }, interval);
    }
    
    /**
     * Отключает автоматическое сохранение
     */
    disableAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }
    
    /**
     * Форматирует оставшееся время в удобный для чтения формат
     * @param {number} timeRemaining - оставшееся время в миллисекундах
     * @returns {string} - форматированная строка времени
     */
    static formatTimeRemaining(timeRemaining) {
        if (timeRemaining <= 0) {
            return "00:00:00";
        }
        
        const days = Math.floor(timeRemaining / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeRemaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeRemaining % (1000 * 60)) / 1000);
        
        if (days > 0) {
            return `${days}д ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
}

/**
 * Создает и возвращает новый экземпляр таймера олимпиады
 */
function createOlympiadTimer(startDateStr, endDateStr, elementIds, onTimeUpdate, onComplete) {
    // Преобразуем строки дат в объекты Date
    const startDate = new Date(startDateStr.replace(/-/g, '/'));
    const endDate = new Date(endDateStr.replace(/-/g, '/'));
    
    // Получаем DOM-элементы таймера
    const elements = {
        container: document.getElementById(elementIds.container || 'olympiad-timer-container'),
        status: document.getElementById(elementIds.status || 'olympiad-status'),
        timerLabel: document.getElementById(elementIds.timerLabel || 'timer-label'),
        days: document.getElementById(elementIds.days || 'days'),
        hours: document.getElementById(elementIds.hours || 'hours'),
        minutes: document.getElementById(elementIds.minutes || 'minutes'),
        seconds: document.getElementById(elementIds.seconds || 'seconds'),
        progressBar: document.getElementById(elementIds.progressBar || 'timer-progress-bar'),
        digits: document.getElementById(elementIds.digits || 'timer-digits')
    };
    
    // Создаем и возвращаем новый экземпляр таймера
    const timer = new OlympiadTimer(
        startDate,
        endDate,
        elements,
        onTimeUpdate,
        onComplete
    );
    
    return timer;
}