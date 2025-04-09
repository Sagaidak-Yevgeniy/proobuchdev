import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def run_code_with_test_case(code, input_data, expected_output, timeout=5):
    """
    Выполняет код с заданными входными данными и проверяет соответствие ожидаемому результату
    
    Args:
        code (str): Код для выполнения
        input_data (str): Входные данные
        expected_output (str): Ожидаемый результат
        timeout (int): Максимальное время выполнения в секундах
        
    Returns:
        tuple: (result, error), где
            result (bool): True, если выходные данные соответствуют ожидаемому результату
            error (str): Сообщение об ошибке, если произошла ошибка, иначе None
    """
    # Создаем буферы для перехвата стандартного ввода/вывода/ошибок
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    # Подменяем стандартный ввод данными из теста
    sys.stdin = io.StringIO(input_data)
    
    # Создаем изолированное пространство имен для выполнения кода
    namespace = {}
    
    try:
        # Выполняем код в изолированном пространстве с ограничением времени
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Запускаем выполнение кода в отдельном потоке с таймаутом
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(exec, code, namespace)
                try:
                    future.result(timeout=timeout)
                except TimeoutError:
                    return False, f"Превышено время выполнения ({timeout} сек)"
        
        # Проверяем, есть ли функция solution в пространстве имен
        if 'solution' not in namespace:
            return False, "Не найдена функция solution"
        
        # Запускаем функцию solution с входными данными и перехватываем вывод
        solution_func = namespace['solution']
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Обрабатываем различные типы входных данных
            try:
                # Если входные данные - это несколько строк, передаем каждую строку как отдельный аргумент
                if '\n' in input_data:
                    args = input_data.strip().split('\n')
                    result = solution_func(*args)
                # Если входные данные - это несколько значений в одной строке, передаем их как отдельные аргументы
                elif ' ' in input_data.strip():
                    args = input_data.strip().split()
                    result = solution_func(*args)
                # Если входная строка пуста, вызываем функцию без аргументов
                elif not input_data.strip():
                    result = solution_func()
                # Иначе передаем всю строку как один аргумент
                else:
                    result = solution_func(input_data.strip())
                
                # Если функция возвращает значение, добавляем его в вывод
                if result is not None:
                    print(result, file=stdout_buffer)
            except Exception as e:
                # Перехватываем ошибки при вызове функции solution
                traceback.print_exc(file=stderr_buffer)
        
        # Получаем результаты выполнения
        stdout_output = stdout_buffer.getvalue().strip()
        stderr_output = stderr_buffer.getvalue().strip()
        
        # Проверяем наличие ошибок
        if stderr_output:
            return False, f"Ошибка выполнения: {stderr_output}"
        
        # Сравниваем результат с ожидаемым выходом (игнорируя пробелы в конце строк)
        expected_lines = [line.rstrip() for line in expected_output.strip().split('\n')]
        actual_lines = [line.rstrip() for line in stdout_output.strip().split('\n')]
        
        if expected_lines == actual_lines:
            return True, None
        else:
            return False, f"Результат не соответствует ожидаемому.\nОжидалось: {expected_output}\nПолучено: {stdout_output}"
        
    except SyntaxError as e:
        # Обрабатываем синтаксические ошибки в коде
        return False, f"Синтаксическая ошибка: {str(e)}"
    except Exception as e:
        # Обрабатываем другие исключения
        return False, f"Ошибка выполнения: {str(e)}"
    finally:
        # Восстанавливаем стандартный ввод
        sys.stdin = sys.__stdin__

def check_assignment(submission):
    """
    Проверяет отправленное решение задания на всех тестовых случаях
    
    Args:
        submission: объект AssignmentSubmission для проверки
    """
    from .models import TestCase
    
    # Обновляем статус на "проверяется"
    submission.status = 'checking'
    submission.save()
    
    # Получаем все тестовые случаи для задания
    test_cases = TestCase.objects.filter(assignment=submission.assignment)
    
    if not test_cases.exists():
        submission.status = 'error'
        submission.feedback = "Для этого задания не созданы тестовые случаи"
        submission.save()
        return
    
    # Проверяем решение на каждом тестовом случае
    passed_tests = 0
    total_tests = test_cases.count()
    all_feedback = []
    
    for test_case in test_cases:
        result, error = run_code_with_test_case(
            submission.code,
            test_case.input_data,
            test_case.expected_output
        )
        
        # Формируем обратную связь по тесту
        if test_case.is_hidden:
            test_info = "Скрытый тест"
        else:
            test_info = f"Тест с входными данными: {test_case.input_data}"
        
        if result:
            passed_tests += 1
            test_feedback = f"{test_info}: Пройден ✓"
        else:
            if test_case.is_hidden:
                test_feedback = f"{test_info}: Не пройден ✗ (проверьте правильность решения)"
            else:
                test_feedback = f"{test_info}: Не пройден ✗\n{error}"
        
        all_feedback.append(test_feedback)
    
    # Вычисляем оценку (процент пройденных тестов)
    if total_tests > 0:
        submission.score = (passed_tests / total_tests) * 100
    
    # Определяем итоговый статус
    if passed_tests == total_tests:
        submission.status = 'passed'
    else:
        submission.status = 'failed'
    
    # Сохраняем обратную связь
    submission.feedback = "\n\n".join(all_feedback)
    submission.save()
