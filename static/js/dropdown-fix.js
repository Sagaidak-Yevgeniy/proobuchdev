/**
 * Улучшенная работа выпадающих меню с помощью JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Находим все группы с выпадающими меню
    const dropdownGroups = document.querySelectorAll('.group');
    
    dropdownGroups.forEach(group => {
        let timeout;
        const dropdown = group.querySelector('.group-hover\\:block');
        
        if (!dropdown) return;
        
        // При наведении на группу
        group.addEventListener('mouseenter', function() {
            clearTimeout(timeout);
            dropdown.style.display = 'block';
            dropdown.style.opacity = '1';
            dropdown.style.visibility = 'visible';
            dropdown.style.transform = 'translateY(0) scale(1)';
            dropdown.style.pointerEvents = 'auto';
        });
        
        // При выходе из группы с задержкой
        group.addEventListener('mouseleave', function() {
            timeout = setTimeout(function() {
                dropdown.style.opacity = '0';
                dropdown.style.visibility = 'hidden';
                dropdown.style.transform = 'translateY(-10px) scale(0.95)';
                dropdown.style.pointerEvents = 'none';
            }, 300); // Задержка в 300 мс перед скрытием
        });
        
        // При наведении на само выпадающее меню
        if (dropdown) {
            dropdown.addEventListener('mouseenter', function() {
                clearTimeout(timeout);
            });
            
            dropdown.addEventListener('mouseleave', function() {
                timeout = setTimeout(function() {
                    dropdown.style.opacity = '0';
                    dropdown.style.visibility = 'hidden';
                    dropdown.style.transform = 'translateY(-10px) scale(0.95)';
                    dropdown.style.pointerEvents = 'none';
                }, 300);
            });
        }
    });
});