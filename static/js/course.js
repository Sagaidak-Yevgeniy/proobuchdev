document.addEventListener('DOMContentLoaded', function() {
    // Плавная прокрутка к секциям
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Обработка фильтров курсов
    const categoryFilters = document.querySelectorAll('.category-filter');
    if (categoryFilters.length > 0) {
        categoryFilters.forEach(filter => {
            filter.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Удаляем активный класс у всех фильтров
                categoryFilters.forEach(f => {
                    f.classList.remove('active-filter');
                });
                
                // Добавляем активный класс к выбранному фильтру
                this.classList.add('active-filter');
                
                // Получаем значение фильтра
                const categorySlug = this.dataset.category;
                
                // Обновляем URL с новым параметром категории
                const url = new URL(window.location);
                if (categorySlug) {
                    url.searchParams.set('category', categorySlug);
                } else {
                    url.searchParams.delete('category');
                }
                window.history.pushState({}, '', url);
                
                // Перезагружаем страницу с новыми параметрами
                window.location.reload();
            });
        });
    }
    
    // Обработка формы поиска
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        const clearSearchButton = searchForm.querySelector('.clear-search');
        
        if (clearSearchButton) {
            clearSearchButton.addEventListener('click', function() {
                searchInput.value = '';
                searchForm.submit();
            });
        }
    }
});
