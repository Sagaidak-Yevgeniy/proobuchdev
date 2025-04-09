import subprocess
import time
import os
import tempfile
import signal
import resource
from contextlib import contextmanager

class TimeoutException(Exception):
    """Исключение, выбрасываемое при превышении времени выполнения кода"""
    pass

@contextmanager
def time_limit(seconds):
    """Контекстный менеджер для ограничения времени выполнения кода"""
    def signal_handler(signum, frame):
        raise TimeoutException("Превышено время выполнения")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def run_code(code, input_data, time_limit_ms=1000, memory_limit_mb=256):
    """
    Выполняет Python-код с заданными входными данными и ограничениями
    
    Args:
        code (str): Python-код для выполнения
        input_data (str): Входные данные для программы
        time_limit_ms (int): Ограничение по времени в миллисекундах
        memory_limit_mb (int): Ограничение по памяти в мегабайтах
        
    Returns:
        dict: Результат выполнения с полями:
            - status: Статус выполнения (accepted, wrong_answer, time_limit и т.д.)
            - output: Вывод программы
            - error: Сообщение об ошибке
            - execution_time: Время выполнения в миллисекундах
    """
    # Создаем временный файл для кода
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as code_file:
        code_file.write(code.encode('utf-8'))
        code_file_path = code_file.name
    
    # Создаем временные файлы для ввода и вывода
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as input_file:
        input_file.write(input_data.encode('utf-8'))
        input_file_path = input_file.name
    
    output_file_path = tempfile.mktemp(suffix='.txt')
    
    result = {
        'status': 'pending',
        'output': '',
        'error': '',
        'execution_time': 0
    }
    
    try:
        # Конвертируем лимиты в секунды и байты
        time_limit_sec = time_limit_ms / 1000
        memory_limit_bytes = memory_limit_mb * 1024 * 1024
        
        # Запускаем процесс с перенаправлением ввода и вывода
        start_time = time.time()
        
        # Функция для установки лимита по памяти
        def set_memory_limit():
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
        
        with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
            try:
                # Запускаем процесс с ограничением времени
                with time_limit(int(time_limit_sec) + 1):  # +1 секунда для запаса
                    process = subprocess.Popen(
                        ['python', code_file_path],
                        stdin=input_file,
                        stdout=output_file,
                        stderr=subprocess.PIPE,
                        preexec_fn=set_memory_limit,
                        text=True
                    )
                    _, stderr = process.communicate()
                    return_code = process.returncode
            except TimeoutException:
                result['status'] = 'time_limit'
                result['error'] = 'Превышено ограничение по времени'
                return result
            except Exception as e:
                result['status'] = 'system_error'
                result['error'] = f'Системная ошибка: {str(e)}'
                return result
        
        execution_time = (time.time() - start_time) * 1000  # в миллисекундах
        result['execution_time'] = int(execution_time)
        
        # Проверяем, успешно ли завершился процесс
        if return_code != 0:
            result['status'] = 'runtime_error'
            result['error'] = stderr.strip()
            return result
        
        # Читаем вывод программы
        with open(output_file_path, 'r') as output_file:
            result['output'] = output_file.read().strip()
        
        # Проверяем время выполнения
        if execution_time > time_limit_ms:
            result['status'] = 'time_limit'
            result['error'] = f'Превышено ограничение по времени ({execution_time:.0f} мс > {time_limit_ms} мс)'
        else:
            result['status'] = 'accepted'
        
    except Exception as e:
        result['status'] = 'system_error'
        result['error'] = f'Системная ошибка: {str(e)}'
    
    finally:
        # Удаляем временные файлы
        for file_path in [code_file_path, input_file_path, output_file_path]:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass
    
    return result


def check_solution(submission):
    """
    Проверяет решение на всех тестовых случаях
    
    Args:
        submission: Объект отправки решения (Submission model)
        
    Returns:
        tuple: (status, points, executed_time, error_message)
    """
    from .models import TestResult
    
    problem = submission.problem
    test_cases = problem.test_cases.all().order_by('order')
    
    passed_tests = 0
    max_execution_time = 0
    last_error = ''
    
    # Помечаем как тестируемую
    submission.status = 'testing'
    submission.save()
    
    for test_case in test_cases:
        result = run_code(
            submission.code,
            test_case.input_data,
            problem.time_limit,
            problem.memory_limit
        )
        
        # Обновляем максимальное время выполнения
        if result['execution_time'] > max_execution_time:
            max_execution_time = result['execution_time']
        
        # Сохраняем результат теста
        test_result = TestResult.objects.create(
            submission=submission,
            test_case=test_case,
            passed=(result['status'] == 'accepted' and result['output'].strip() == test_case.expected_output.strip()),
            execution_time=result['execution_time'],
            output=result['output'],
            error_message=result['error']
        )
        
        # Если тест пройден
        if test_result.passed:
            passed_tests += 1
        else:
            # Сохраняем последнюю ошибку
            last_error = result['error'] if result['error'] else f"Неправильный ответ на тест {test_case.order}"
            
            # Устанавливаем статус на основе ошибки
            if result['status'] != 'accepted':
                submission.status = result['status']
                break
            else:
                submission.status = 'wrong_answer'
    
    # Если все тесты пройдены
    if passed_tests == test_cases.count():
        submission.status = 'accepted'
        submission.points = problem.points
    # Частичное прохождение
    elif passed_tests > 0:
        submission.status = 'wrong_answer'
        # Рассчитываем баллы пропорционально количеству пройденных тестов
        submission.points = int(problem.points * (passed_tests / test_cases.count()))
    
    submission.executed_time = max_execution_time
    submission.error_message = last_error
    submission.save()
    
    # Обновляем статистику участника
    try:
        participant = submission.olympiad.participants.get(user=submission.user)
        participant.update_statistics()
    except:
        pass
    
    return (submission.status, submission.points, max_execution_time, last_error)