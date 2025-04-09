document.addEventListener('DOMContentLoaded', function() {
    // Переключатель мобильных фильтров
    const toggleFiltersBtn = document.getElementById('toggle-filters');
    const filterContent = document.getElementById('filter-content');
    const filterIcon = document.getElementById('filter-icon');
    
    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', function() {
            if (filterContent.classList.contains('hidden')) {
                filterContent.classList.remove('hidden');
                filterIcon.classList.remove('fa-chevron-down');
                filterIcon.classList.add('fa-chevron-up');
            } else {
                filterContent.classList.add('hidden');
                filterIcon.classList.remove('fa-chevron-up');
                filterIcon.classList.add('fa-chevron-down');
            }
        });
    }
    
    // На мобильных начинаем со скрытого фильтра
    if (window.innerWidth < 1024 && filterContent) {
        filterContent.classList.add('hidden');
    }
    
    // Обработка изменения размера окна
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 1024 && filterContent) {
            filterContent.classList.remove('hidden');
        } else if (filterContent) {
            filterContent.classList.add('hidden');
        }
    });
});