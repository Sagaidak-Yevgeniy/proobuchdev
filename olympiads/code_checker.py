import sys
import io
import traceback
import subprocess
import threading
import tempfile
import os
import signal
import resource
from datetime import datetime

def run_code_with_test_case(code, input_data, expected_output, time_limit=1000, memory_limit=256):
    """
    Выполняет код с заданными входными данными и проверяет соответствие ожидаемому результату
    
    Args:
        code (str): Код для выполнения
        input_data (str): Входные данные
        expected_output (str): Ожидаемый результат
        time_limit (int): Максимальное время выполнения в миллисекундах
        memory_limit (int): Максимальное использование памяти в МБ
        
    Returns:
        dict: Результат выполнения с полями:
            - passed (bool): True, если выходные данные соответствуют ожидаемому результату
            - execution_time (int): Время выполнения в миллисекундах или None при ошибке
            - memory_used (int): Используемая память в КБ или None при ошибке
            - output (str): Выходные данные программы или None при ошибке
            - error (str): Сообщение об ошибке или None при успешном выполнении
            - status (str): Статус выполнения ('accepted', 'wrong_answer', 'time_limit', 'memory_limit', 'runtime_error', 'system_error')
    """
    # Преобразуем ограничения
    time_limit_seconds = time_limit / 1000  # из мс в секунды
    memory_limit_bytes = memory_limit * 1024 * 1024  # из МБ в байты

    # Создаем временный файл для кода
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_filename = temp_file.name
        temp_file.write(code.encode('utf-8'))
    
    result = {
        'passed': False,
        'execution_time': None,
        'memory_used': None,
        'output': None,
        'error': None,
        'status': 'pending'
    }
    
    try:
        # Создаем процесс
        start_time = datetime.now()
        
        # Подготавливаем ввод
        process = subprocess.Popen(
            [sys.executable, temp_filename],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=set_limits(time_limit_seconds, memory_limit_bytes)
        )
        
        # Отправляем входные данные и получаем результат с таймаутом
        stdout, stderr = process.communicate(input=input_data, timeout=time_limit_seconds + 0.5)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds() * 1000  # в миллисекундах
        
        # Проверяем статус
        if process.returncode != 0:
            if process.returncode == -9:  # SIGKILL (превышение лимита памяти)
                result['status'] = 'memory_limit'
                result['error'] = 'Превышен лимит памяти'
            elif process.returncode == -signal.SIGXCPU:  # Превышение лимита CPU
                result['status'] = 'time_limit'
                result['error'] = 'Превышен лимит времени выполнения'
            else:
                result['status'] = 'runtime_error'
                result['error'] = stderr
        else:
            # Нормализуем выходные данные (удаляем лишние пробелы и переносы строк)
            normalized_output = stdout.strip()
            normalized_expected = expected_output.strip()
            
            result['output'] = normalized_output
            result['execution_time'] = int(execution_time)
            
            if normalized_output == normalized_expected:
                result['passed'] = True
                result['status'] = 'accepted'
            else:
                result['status'] = 'wrong_answer'
                result['error'] = f'Ожидаемый вывод:\n{normalized_expected}\n\nФактический вывод:\n{normalized_output}'
        
    except subprocess.TimeoutExpired:
        result['status'] = 'time_limit'
        result['error'] = 'Превышен лимит времени выполнения'
        process.kill()
    except Exception as e:
        result['status'] = 'system_error'
        result['error'] = f'Системная ошибка: {str(e)}\n{traceback.format_exc()}'
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_filename)
        except:
            pass
    
    return result


def set_limits(time_limit_seconds, memory_limit_bytes):
    """Устанавливает ограничения ресурсов для процесса"""
    def limit_resources():
        # Устанавливаем ограничение на использование CPU
        resource.setrlimit(resource.RLIMIT_CPU, (int(time_limit_seconds) + 1, int(time_limit_seconds) + 1))
        # Устанавливаем ограничение на использование памяти
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
    
    return limit_resources


def check_submission(submission):
    """
    Проверяет отправленное решение задачи на всех тестовых случаях
    
    Args:
        submission: объект Submission для проверки
    
    Returns:
        bool: True если проверка прошла успешно
    """
    from .models import TestResult
    
    # Обновляем статус отправки
    submission.status = 'testing'
    submission.save(update_fields=['status'])
    
    # Получаем все тестовые случаи для задачи
    test_cases = submission.problem.test_cases.all().order_by('order')
    
    # Удаляем прошлые результаты тестов, если есть
    submission.test_results.all().delete()
    
    # Получаем общее количество и сумму весов тестов
    total_tests = test_cases.count()
    total_weight = sum(test_case.weight for test_case in test_cases)
    
    # Инициализируем переменные для подсчета
    passed_tests = 0
    total_weighted_score = 0
    max_execution_time = 0
    
    # Проверяем решение на каждом тестовом случае
    for test_case in test_cases:
        result = run_code_with_test_case(
            code=submission.code,
            input_data=test_case.input_data,
            expected_output=test_case.expected_output,
            time_limit=submission.problem.time_limit,
            memory_limit=submission.problem.memory_limit
        )
        
        # Создаем запись о результате теста
        test_result = TestResult(
            submission=submission,
            test_case=test_case,
            passed=result['passed'],
            execution_time=result['execution_time'],
            memory_used=result.get('memory_used'),
            output=result.get('output', ''),
            error_message=result.get('error', '')
        )
        test_result.save()
        
        # Обновляем счетчики
        if result['passed']:
            passed_tests += 1
            total_weighted_score += test_case.weight
        
        # Обновляем максимальное время выполнения
        if result['execution_time'] and result['execution_time'] > max_execution_time:
            max_execution_time = result['execution_time']
        
        # Если произошла ошибка (кроме неправильного ответа), прерываем проверку
        if result['status'] not in ['accepted', 'wrong_answer']:
            submission.status = result['status']
            submission.error_message = result['error']
            submission.executed_time = result['execution_time']
            submission.points = 0
            submission.save(update_fields=['status', 'error_message', 'executed_time', 'points'])
            return False
    
    # Если все тесты пройдены, считаем решение принятым
    if passed_tests == total_tests:
        submission.status = 'accepted'
        submission.points = submission.problem.points
    else:
        # Если есть непройденные тесты, считаем решение частично правильным
        submission.status = 'wrong_answer'
        if total_weight > 0:
            # Вычисляем очки по весам тестов
            percentage = total_weighted_score / total_weight
            submission.points = int(percentage * submission.problem.points)
            
            # Обновляем статус, если пользователь набрал хоть какие-то баллы
            if submission.points > 0:
                submission.status = 'partial'
        else:
            submission.points = 0
    
    submission.executed_time = max_execution_time
    submission.save(update_fields=['status', 'points', 'executed_time'])
    
    return True


def check_code_safety(code):
    """
    Проверяет код на наличие потенциально опасных операций
    
    Args:
        code (str): Код для проверки
        
    Returns:
        tuple: (is_safe, message) где
            is_safe (bool): True, если код не содержит запрещенных операций
            message (str): Сообщение о нарушении безопасности или None
    """
    # Запрещенные импорты и операции
    forbidden = [
        'import os', 'from os import', 
        'import sys', 'from sys import',
        'import subprocess', 'from subprocess import',
        'import shutil', 'from shutil import',
        '__import__', 'eval(', 'exec(', 
        'open(', 'file(', 
        'import socket', 'from socket import'
    ]
    
    # Проверяем наличие запрещенных операций
    for item in forbidden:
        if item in code:
            return False, f"Запрещено использование: {item}"
    
    return True, None