document.addEventListener('DOMContentLoaded', function() {
    // Инициализация CodeMirror для редактора кода
    const codeEditor = document.querySelector('.code-editor');
    
    if (codeEditor) {
        const editor = CodeMirror.fromTextArea(codeEditor, {
            mode: 'python',
            theme: 'monokai',
            lineNumbers: true,
            indentUnit: 4,
            indentWithTabs: false,
            matchBrackets: true,
            autoCloseBrackets: true,
            extraKeys: {
                "Tab": function(cm) {
                    cm.replaceSelection("    ", "end");
                }
            }
        });
        
        // Автоматически фокусируемся на редакторе
        setTimeout(function() {
            editor.focus();
        }, 100);
        
        // Обновляем содержимое поля textarea перед отправкой формы
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                // Убедимся, что CodeMirror обновляет textarea перед отправкой
                editor.save();
                
                // Проверяем, что код не пустой
                if (!codeEditor.value || codeEditor.value.trim() === '') {
                    e.preventDefault();
                    alert('Пожалуйста, введите код для решения задания.');
                    return false;
                }
            });
        }
        
        // Добавляем обработчик для кнопки отправки, если форма не найдена
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton && !form) {
            submitButton.addEventListener('click', function() {
                editor.save();
                const submissionForm = document.getElementById('submission-form');
                if (submissionForm) {
                    submissionForm.submit();
                }
            });
        }
    }
    
    // Подсветка синтаксиса для предварительного просмотра кода
    document.querySelectorAll('pre code').forEach(function(codeBlock) {
        if (codeBlock.className === '') {
            codeBlock.className = 'language-python';
        }
    });
});
