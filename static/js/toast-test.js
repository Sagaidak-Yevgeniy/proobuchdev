// Вспомогательный файл для системы уведомлений
document.addEventListener('DOMContentLoaded', function() {
    // Ждем загрузки компонента toast
    if (!window.showToast) {
        // Ожидаем событие toastReady
        document.addEventListener('toastReady', function() {
            console.log('Toast компонент инициализирован');
        });
    }
});