#!/usr/bin/env python
"""
Тестирование адаптивности интерфейса и UI/UX 
образовательной платформы
"""

import os
import sys
import django
import time
import json
from datetime import datetime

# Настраиваем окружение Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

# Импортируем необходимые модули Django
from django.test import LiveServerTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

# Импортируем модели проекта
from courses.models import Course, Category, Lesson, LessonContent
from olympiads.models import Olympiad, OlympiadTask
from users.models import CustomUser

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium не установлен. Визуальное тестирование недоступно.")


class UITester:
    """Тестирование пользовательского интерфейса и отзывчивого дизайна"""
    
    def __init__(self):
        self.client = Client()
        self.test_users = {}
        self.test_results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'visual_report': []
        }
        
        # Устройства для тестирования адаптивности
        self.devices = [
            {'name': 'iPhone SE', 'width': 375, 'height': 667},
            {'name': 'iPhone XR', 'width': 414, 'height': 896},
            {'name': 'iPad', 'width': 768, 'height': 1024},
            {'name': 'Laptop', 'width': 1366, 'height': 768},
            {'name': 'Desktop', 'width': 1920, 'height': 1080}
        ]

        # Основные страницы для тестирования
        self.pages_to_test = [
            {'name': 'Главная страница', 'url': '/'},
            {'name': 'Список курсов', 'url': '/courses/'},
            {'name': 'Список олимпиад', 'url': '/olympiads/'},
            {'name': 'Управление олимпиадами', 'url': '/olympiads/manage/'},
            {'name': 'Профиль пользователя', 'url': '/users/profile/'},
            {'name': 'Панель администратора', 'url': '/admin/'}
        ]

        # UI/UX компоненты для тестирования
        self.ui_components = [
            {'name': 'Навигационное меню', 'selector': 'nav'},
            {'name': 'Кнопки', 'selector': 'button, .btn'},
            {'name': 'Формы', 'selector': 'form'},
            {'name': 'Карточки курсов', 'selector': '.course-card'},
            {'name': 'Карточки олимпиад', 'selector': '.olympiad-card'},
            {'name': 'Выпадающее меню', 'selector': '.dropdown'},
            {'name': 'Модальные окна', 'selector': '.modal'},
            {'name': 'Уведомления', 'selector': '.notification'}
        ]
        
        # Пытаемся инициализировать Selenium WebDriver, если установлен
        self.driver = None
        if SELENIUM_AVAILABLE:
            try:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=options)
                self.driver.set_window_size(1920, 1080)
                print("Selenium WebDriver успешно инициализирован")
            except Exception as e:
                print(f"Не удалось инициализировать Selenium WebDriver: {e}")
                self.driver = None
    
    def setup_test_users(self):
        """Создание тестовых пользователей для UI тестирования"""
        User = get_user_model()
        
        # Создаем администратора
        admin, created = User.objects.get_or_create(
            username='admin_ui_test',
            defaults={
                'email': 'admin_ui_test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
        self.test_users['admin'] = admin
        
        # Создаем студента
        student, created = User.objects.get_or_create(
            username='student_ui_test',
            defaults={
                'email': 'student_ui_test@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            student.set_password('student12345')
            student.save()
        self.test_users['student'] = student
        
        # Создаем преподавателя
        teacher, created = User.objects.get_or_create(
            username='teacher_ui_test',
            defaults={
                'email': 'teacher_ui_test@example.com',
                'is_staff': True,
                'is_superuser': False,
                'is_teacher': True
            }
        )
        if created:
            teacher.set_password('teacher12345')
            teacher.save()
        self.test_users['teacher'] = teacher
        
        print(f"Тестовые пользователи созданы: {', '.join(self.test_users.keys())}")
    
    def test_responsive_design(self):
        """Тестирование адаптивного дизайна для разных устройств"""
        print("\nПроверка адаптивного дизайна для разных устройств...")
        
        if not self.driver:
            self.test_results['warnings'].append('Selenium не доступен для проверки адаптивности')
            print("⚠ Selenium не доступен. Визуальное тестирование недоступно.")
            return
        
        # Авторизуемся как администратор
        self.client.login(username='admin_ui_test', password='admin12345')
        
        for device in self.devices:
            print(f"\nТестирование на устройстве: {device['name']} ({device['width']}x{device['height']})")
            
            # Устанавливаем размер окна браузера
            self.driver.set_window_size(device['width'], device['height'])
            
            for page in self.pages_to_test:
                try:
                    url = page['url']
                    print(f"  Проверка страницы: {page['name']} ({url})")
                    
                    # Открываем страницу
                    self.driver.get(f"http://localhost:8000{url}")
                    time.sleep(1)  # Ждем загрузку страницы
                    
                    # Проверяем видимость ключевых элементов
                    header_visible = self._is_element_visible('header')
                    nav_visible = self._is_element_visible('nav')
                    burger_menu = self._is_element_visible('.burger-menu') or self._is_element_visible('.navbar-toggler')
                    
                    # На мобильных устройствах должно быть бургер-меню
                    if device['width'] < 768:
                        if burger_menu:
                            self.test_results['passed'].append(f"Бургер-меню на {page['name']} для {device['name']}")
                            print(f"    ✓ Бургер-меню отображается корректно")
                        else:
                            self.test_results['failed'].append(f"Отсутствие бургер-меню на {page['name']} для {device['name']}")
                            print(f"    ✗ Бургер-меню не найдено")
                    
                    # Проверяем, что контент не выходит за границы экрана
                    overflow = self._check_horizontal_overflow()
                    if overflow:
                        self.test_results['failed'].append(f"Горизонтальный скролл на {page['name']} для {device['name']}")
                        print(f"    ✗ Обнаружен горизонтальный скролл")
                    else:
                        self.test_results['passed'].append(f"Отсутствие горизонтального скролла на {page['name']} для {device['name']}")
                        print(f"    ✓ Нет горизонтального скролла")
                    
                    # Проверяем интерактивные элементы
                    buttons = self._get_interactive_elements('button, .btn')
                    if buttons:
                        self.test_results['passed'].append(f"Кнопки на {page['name']} для {device['name']}")
                        print(f"    ✓ Найдено {len(buttons)} кнопок")
                    else:
                        self.test_results['warnings'].append(f"Отсутствие кнопок на {page['name']} для {device['name']}")
                        print(f"    ⚠ Кнопки не найдены")
                    
                    # Сохраняем скриншот
                    screenshot_dir = 'ui_test_screenshots'
                    if not os.path.exists(screenshot_dir):
                        os.makedirs(screenshot_dir)
                    
                    screenshot_path = f"{screenshot_dir}/{device['name'].replace(' ', '_')}_{page['name'].replace(' ', '_')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"    Скриншот сохранен: {screenshot_path}")
                    
                except Exception as e:
                    self.test_results['failed'].append(f"Тестирование {page['name']} для {device['name']} (ошибка)")
                    print(f"    ✗ Ошибка при тестировании: {e}")
        
        # Возвращаем браузер к полному размеру
        self.driver.set_window_size(1920, 1080)
    
    def test_ui_components(self):
        """Проверка UI компонентов и их стилей"""
        print("\nПроверка UI компонентов и их стилей...")
        
        if not self.driver:
            self.test_results['warnings'].append('Selenium не доступен для проверки UI компонентов')
            print("⚠ Selenium не доступен. Визуальное тестирование UI компонентов недоступно.")
            return
        
        # Авторизуемся как администратор
        self.client.login(username='admin_ui_test', password='admin12345')
        
        for page in self.pages_to_test:
            try:
                url = page['url']
                print(f"Проверка UI компонентов на странице: {page['name']} ({url})")
                
                # Открываем страницу
                self.driver.get(f"http://localhost:8000{url}")
                time.sleep(1)  # Ждем загрузку страницы
                
                for component in self.ui_components:
                    elements = self._get_interactive_elements(component['selector'])
                    if elements:
                        self.test_results['passed'].append(f"{component['name']} на {page['name']}")
                        print(f"  ✓ {component['name']}: найдено {len(elements)} элементов")
                        
                        # Проверяем доступность (размер достаточный для взаимодействия)
                        small_elements = []
                        for element in elements:
                            size = element.size
                            if size['width'] < 40 or size['height'] < 40:
                                small_elements.append(element)
                        
                        if small_elements:
                            self.test_results['warnings'].append(f"Маленькие элементы {component['name']} на {page['name']}")
                            print(f"  ⚠ Найдено {len(small_elements)} элементов малого размера (менее 40px)")
                    else:
                        self.test_results['warnings'].append(f"Отсутствие {component['name']} на {page['name']}")
                        print(f"  ⚠ {component['name']} не найдены")
                
            except Exception as e:
                self.test_results['failed'].append(f"Проверка UI компонентов на {page['name']} (ошибка)")
                print(f"  ✗ Ошибка при проверке UI компонентов: {e}")
    
    def test_ux_interactions(self):
        """Проверка взаимодействия с пользователем (UX)"""
        print("\nПроверка пользовательского опыта (UX)...")
        
        if not self.driver:
            self.test_results['warnings'].append('Selenium не доступен для проверки UX')
            print("⚠ Selenium не доступен. Тестирование UX недоступно.")
            return
        
        # Авторизуемся как студент
        self.client.login(username='student_ui_test', password='student12345')
        
        # Тест навигации между страницами
        try:
            print("Проверка навигации...")
            self.driver.get("http://localhost:8000/")
            time.sleep(1)
            
            # Находим ссылки на курсы и переходим
            course_link = self._get_link_by_text("Курсы")
            if course_link:
                course_link.click()
                time.sleep(1)
                
                if "courses" in self.driver.current_url:
                    self.test_results['passed'].append("Навигация на страницу курсов")
                    print("  ✓ Навигация на страницу курсов работает")
                else:
                    self.test_results['failed'].append("Навигация на страницу курсов")
                    print("  ✗ Ошибка навигации на страницу курсов")
            else:
                self.test_results['warnings'].append("Ссылка на курсы не найдена")
                print("  ⚠ Ссылка на страницу курсов не найдена")
            
            # Возвращаемся на главную
            self.driver.get("http://localhost:8000/")
            time.sleep(1)
            
            # Проверяем навигацию на страницу олимпиад
            olympiad_link = self._get_link_by_text("Олимпиады")
            if olympiad_link:
                olympiad_link.click()
                time.sleep(1)
                
                if "olympiads" in self.driver.current_url:
                    self.test_results['passed'].append("Навигация на страницу олимпиад")
                    print("  ✓ Навигация на страницу олимпиад работает")
                else:
                    self.test_results['failed'].append("Навигация на страницу олимпиад")
                    print("  ✗ Ошибка навигации на страницу олимпиад")
            else:
                self.test_results['warnings'].append("Ссылка на олимпиады не найдена")
                print("  ⚠ Ссылка на страницу олимпиад не найдена")
        
        except Exception as e:
            self.test_results['failed'].append("Тестирование навигации (ошибка)")
            print(f"  ✗ Ошибка при тестировании навигации: {e}")
        
        # Тест форм
        try:
            print("Проверка форм...")
            self.driver.get("http://localhost:8000/users/profile/")
            time.sleep(1)
            
            # Находим форму профиля
            form = self.driver.find_element(By.TAG_NAME, "form")
            if form:
                self.test_results['passed'].append("Наличие формы профиля")
                print("  ✓ Форма профиля найдена")
                
                # Проверяем поля формы
                inputs = form.find_elements(By.TAG_NAME, "input")
                if inputs:
                    self.test_results['passed'].append("Поля формы профиля")
                    print(f"  ✓ Найдено {len(inputs)} полей ввода")
                else:
                    self.test_results['warnings'].append("Отсутствие полей в форме профиля")
                    print("  ⚠ Поля ввода не найдены")
            else:
                self.test_results['warnings'].append("Форма профиля не найдена")
                print("  ⚠ Форма профиля не найдена")
                
        except Exception as e:
            self.test_results['failed'].append("Тестирование форм (ошибка)")
            print(f"  ✗ Ошибка при тестировании форм: {e}")
        
        # Тест отзывчивости элементов
        try:
            print("Проверка отзывчивости элементов...")
            self.driver.get("http://localhost:8000/")
            time.sleep(1)
            
            # Проверяем кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                # Выбираем первую видимую кнопку
                for button in buttons:
                    if button.is_displayed():
                        # Запоминаем стили до наведения
                        original_style = button.get_attribute("style")
                        
                        # Наводим мышь
                        webdriver.ActionChains(self.driver).move_to_element(button).perform()
                        time.sleep(0.5)
                        
                        # Получаем стили после наведения
                        hover_style = button.get_attribute("style")
                        
                        if original_style != hover_style:
                            self.test_results['passed'].append("Отзывчивость кнопок при наведении")
                            print("  ✓ Кнопки реагируют на наведение")
                        else:
                            # Проверяем через JavaScript, т.к. некоторые эффекты могут быть не в атрибуте style
                            has_hover = self.driver.execute_script("""
                                var style = window.getComputedStyle(arguments[0], ':hover');
                                return style.backgroundColor !== window.getComputedStyle(arguments[0]).backgroundColor;
                            """, button)
                            
                            if has_hover:
                                self.test_results['passed'].append("Отзывчивость кнопок при наведении")
                                print("  ✓ Кнопки реагируют на наведение (через CSS)")
                            else:
                                self.test_results['warnings'].append("Отсутствие эффекта при наведении на кнопки")
                                print("  ⚠ Кнопки не реагируют на наведение")
                        
                        break
            else:
                self.test_results['warnings'].append("Кнопки не найдены для проверки отзывчивости")
                print("  ⚠ Кнопки не найдены для проверки отзывчивости")
                
        except Exception as e:
            self.test_results['failed'].append("Тестирование отзывчивости (ошибка)")
            print(f"  ✗ Ошибка при тестировании отзывчивости: {e}")
    
    def test_theme_support(self):
        """Проверка поддержки светлой/темной темы"""
        print("\nПроверка поддержки светлой/темной темы...")
        
        if not self.driver:
            self.test_results['warnings'].append('Selenium не доступен для проверки темы')
            print("⚠ Selenium не доступен. Тестирование темы недоступно.")
            return
        
        try:
            # Проверяем наличие переключателя темы
            self.driver.get("http://localhost:8000/")
            time.sleep(1)
            
            theme_toggle = None
            # Ищем по разным селекторам, которые могут использоваться для переключателя темы
            for selector in ['.theme-toggle', '#theme-toggle', '[data-theme-toggle]', '.dark-mode-toggle']:
                try:
                    theme_toggle = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if theme_toggle:
                        break
                except:
                    continue
            
            if theme_toggle:
                self.test_results['passed'].append("Наличие переключателя темы")
                print("  ✓ Переключатель темы найден")
                
                # Проверяем работу переключателя
                initial_theme = self.driver.execute_script('return document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");')
                
                # Кликаем по переключателю
                theme_toggle.click()
                time.sleep(1)
                
                after_click_theme = self.driver.execute_script('return document.documentElement.classList.contains("dark") || document.body.classList.contains("dark");')
                
                if initial_theme != after_click_theme:
                    self.test_results['passed'].append("Работа переключателя темы")
                    print("  ✓ Переключатель темы работает")
                else:
                    # Проверяем атрибут data-theme
                    initial_data_theme = self.driver.execute_script('return document.documentElement.getAttribute("data-theme") || document.body.getAttribute("data-theme");')
                    
                    # Кликаем снова
                    theme_toggle.click()
                    time.sleep(1)
                    
                    after_click_data_theme = self.driver.execute_script('return document.documentElement.getAttribute("data-theme") || document.body.getAttribute("data-theme");')
                    
                    if initial_data_theme != after_click_data_theme:
                        self.test_results['passed'].append("Работа переключателя темы (через data-theme)")
                        print("  ✓ Переключатель темы работает (через data-theme)")
                    else:
                        self.test_results['warnings'].append("Переключатель темы не изменяет тему")
                        print("  ⚠ Переключатель темы не изменяет тему")
            else:
                self.test_results['warnings'].append("Переключатель темы не найден")
                print("  ⚠ Переключатель темы не найден")
                
        except Exception as e:
            self.test_results['warnings'].append("Тестирование темы (ошибка)")
            print(f"  ✗ Ошибка при тестировании темы: {e}")
    
    def generate_report(self):
        """Генерация отчета о проверке UI/UX"""
        print("\nГенерация отчета о проверке UI/UX...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': self.test_results,
            'summary': {
                'passed': len(self.test_results['passed']),
                'failed': len(self.test_results['failed']),
                'warnings': len(self.test_results['warnings']),
                'total': len(self.test_results['passed']) + len(self.test_results['failed'])
            }
        }
        
        # Вычисляем процент успешных тестов
        if report['summary']['total'] > 0:
            report['summary']['success_rate'] = (report['summary']['passed'] / report['summary']['total']) * 100
        else:
            report['summary']['success_rate'] = 0
        
        # Записываем отчет в файл
        report_dir = 'ui_test_reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        report_file = f"{report_dir}/ui_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
        
        print(f"Отчет сохранен в файл: {report_file}")
        
        # Выводим сводку результатов
        print("\n" + "="*50)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ UI/UX")
        print("="*50)
        
        print(f"\nУспешно пройденных тестов: {report['summary']['passed']}")
        print(f"Неудачных тестов: {report['summary']['failed']}")
        print(f"Предупреждений: {report['summary']['warnings']}")
        print(f"Общий процент успеха: {report['summary']['success_rate']:.1f}%")
        
        if report['summary']['success_rate'] >= 90:
            print("\nUI/UX соответствует современным стандартам ✓")
        elif report['summary']['success_rate'] >= 70:
            print("\nUI/UX требует некоторых улучшений ⚠")
        else:
            print("\nUI/UX требует значительной доработки ✗")
    
    def run_tests(self):
        """Запуск всех UI/UX тестов"""
        print("Начало тестирования UI/UX...")
        
        # Создаем тестовых пользователей
        self.setup_test_users()
        
        # Тестируем адаптивный дизайн
        self.test_responsive_design()
        
        # Тестируем UI компоненты
        self.test_ui_components()
        
        # Тестируем UX взаимодействия
        self.test_ux_interactions()
        
        # Тестируем поддержку тем
        self.test_theme_support()
        
        # Генерируем отчет
        self.generate_report()
        
        # Закрываем Selenium драйвер, если он был инициализирован
        if self.driver:
            self.driver.quit()
            print("Selenium WebDriver закрыт")
    
    # Вспомогательные методы для работы с Selenium
    
    def _is_element_visible(self, selector):
        """Проверяет, виден ли элемент на странице"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.is_displayed()
        except:
            return False
    
    def _check_horizontal_overflow(self):
        """Проверяет наличие горизонтального скролла на странице"""
        return self.driver.execute_script(
            "return document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
    
    def _get_interactive_elements(self, selector):
        """Получает список интерактивных элементов по селектору"""
        try:
            return self.driver.find_elements(By.CSS_SELECTOR, selector)
        except:
            return []
    
    def _get_link_by_text(self, text):
        """Находит ссылку по тексту"""
        try:
            return self.driver.find_element(By.XPATH, f"//a[contains(text(), '{text}')]")
        except:
            return None

# Запускаем тестирование UI/UX
if __name__ == '__main__':
    tester = UITester()
    tester.run_tests()