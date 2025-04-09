document.addEventListener('DOMContentLoaded', function() {
    // Обработка переключения между уроками в боковом меню
    const lessonLinks = document.querySelectorAll('.lesson-link');
    
    lessonLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Если это не ссылка для открытия урока
            if (this.classList.contains('lesson-toggle')) {
                e.preventDefault();
                
                // Получаем родительский элемент (элемент урока)
                const lessonItem = this.closest('.lesson-item');
                
                // Переключаем отображение содержимого урока
                const lessonContent = lessonItem.querySelector('.lesson-content');
                lessonContent.classList.toggle('hidden');
                
                // Меняем иконку
                const icon = this.querySelector('i');
                if (icon.classList.contains('fa-chevron-down')) {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        });
    });
    
    // Подсветка синтаксиса для блоков кода
    document.querySelectorAll('.content-code pre code').forEach(function(codeBlock) {
        if (codeBlock.className === '') {
            codeBlock.className = 'language-python';
        }
    });
    
    // Обработка переключения вкладок содержимого
    const contentTabs = document.querySelectorAll('.content-tab');
    
    contentTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const contentType = this.dataset.contentType;
            
            // Удаляем активный класс у всех вкладок
            contentTabs.forEach(t => {
                t.classList.remove('active-tab');
            });
            
            // Добавляем активный класс к выбранной вкладке
            this.classList.add('active-tab');
            
            // Скрываем всё содержимое
            document.querySelectorAll('.content-panel').forEach(panel => {
                panel.classList.add('hidden');
            });
            
            // Показываем выбранное содержимое
            document.querySelector(`.content-panel[data-content-type="${contentType}"]`).classList.remove('hidden');
        });
    });
    
    // Обработка отметки урока как завершенного
    const completeButton = document.getElementById('complete-lesson');
    
    if (completeButton) {
        completeButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const form = document.getElementById('complete-lesson-form');
            if (form) {
                form.submit();
            }
        });
    }
});
