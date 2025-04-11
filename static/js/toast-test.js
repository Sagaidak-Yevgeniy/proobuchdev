// Тестовый файл для проверки системы уведомлений
document.addEventListener('DOMContentLoaded', function() {
    // Ждем загрузки компонента toast
    if (window.showToast) {
        console.log('Toast компонент готов, добавляем тестовую кнопку');
        addTestButton();
    } else {
        console.log('Ждем загрузки toast компонента...');
        // Ожидаем событие toastReady
        document.addEventListener('toastReady', function() {
            console.log('Toast компонент загружен через событие, добавляем тестовую кнопку');
            addTestButton();
        });
    }

    function addTestButton() {
        // Создаем тестовую кнопку для вызова уведомлений
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'fixed bottom-4 left-4 z-50 flex flex-col space-y-2';
        buttonContainer.setAttribute('id', 'toast-test-buttons');
        
        // Добавляем кнопки для разных типов уведомлений
        const types = ['info', 'success', 'warning', 'error'];
        types.forEach(type => {
            const button = document.createElement('button');
            button.innerText = 'Тест ' + type;
            button.className = `px-4 py-2 rounded-lg shadow-md text-white font-medium text-sm 
                                transition-transform transform hover:scale-105 focus:outline-none
                                ${type === 'info' ? 'bg-blue-500 hover:bg-blue-600' : 
                                 type === 'success' ? 'bg-green-500 hover:bg-green-600' : 
                                 type === 'warning' ? 'bg-yellow-500 hover:bg-yellow-600' : 
                                 'bg-red-500 hover:bg-red-600'}`;
            
            button.addEventListener('click', function() {
                console.log(`Отправляем тестовое уведомление типа: ${type}`);
                window.showToast(`Тестовое уведомление типа ${type}`, type);
            });
            
            buttonContainer.appendChild(button);
        });
        
        // Добавляем контейнер с кнопками на страницу
        document.body.appendChild(buttonContainer);
        console.log('Тестовые кнопки добавлены');
    }
});