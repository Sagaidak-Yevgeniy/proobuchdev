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
        document.querySelector('form').addEventListener('submit', function() {
            editor.save();
        });
    }
    
    // Подсветка синтаксиса для предварительного просмотра кода
    document.querySelectorAll('pre code').forEach(function(codeBlock) {
        if (codeBlock.className === '') {
            codeBlock.className = 'language-python';
        }
    });
});
