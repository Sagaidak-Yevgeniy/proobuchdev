import os
import subprocess
import tempfile
import time
import signal
import resource
import json
from typing import Dict, List, Optional, Tuple, Any

# Константы для ограничений
DEFAULT_TIME_LIMIT = 5  # секунд
DEFAULT_MEMORY_LIMIT = 128 * 1024 * 1024  # 128 MB в байтах
MAX_OUTPUT_LENGTH = 100 * 1024  # 100 KB

# Классы для исключений
class ExecutionError(Exception):
    """Базовый класс для ошибок выполнения"""
    pass

class CompilationError(ExecutionError):
    """Ошибка компиляции"""
    pass

class ExecutionTimeLimitExceeded(ExecutionError):
    """Превышено ограничение времени выполнения"""
    pass

class ExecutionMemoryLimitExceeded(ExecutionError):
    """Превышено ограничение памяти"""
    pass

class ExecutionRuntimeError(ExecutionError):
    """Ошибка времени выполнения"""
    pass

# Конфигурация для разных языков
LANGUAGE_CONFIG = {
    'python': {
        'file_ext': '.py',
        'compile_cmd': None,
        'run_cmd': ['python', '{file}'],
        'format_cmd': ['black', '-q', '{file}'],
    },
    'javascript': {
        'file_ext': '.js',
        'compile_cmd': None,
        'run_cmd': ['node', '{file}'],
        'format_cmd': ['prettier', '--write', '{file}'],
    },
    'java': {
        'file_ext': '.java',
        'compile_cmd': ['javac', '{file}'],
        'run_cmd': ['java', '-cp', '{dir}', 'Main'],
        'format_cmd': ['google-java-format', '-i', '{file}'],
        'main_class': 'Main',
    },
    'cpp': {
        'file_ext': '.cpp',
        'compile_cmd': ['g++', '-std=c++17', '-o', '{dir}/a.out', '{file}'],
        'run_cmd': ['{dir}/a.out'],
        'format_cmd': ['clang-format', '-i', '{file}'],
    }
}

def create_temp_file(code: str, language: str) -> Tuple[str, str, str]:
    """
    Создает временный файл с кодом и возвращает путь к файлу и директории
    
    Args:
        code: Исходный код
        language: Язык программирования
    
    Returns:
        Кортеж из (путь_к_файлу, имя_файла, директория)
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        raise ValueError(f"Неподдерживаемый язык: {language}")
    
    # Для Java создаем файл с именем Main.java
    if language == 'java':
        file_name = f"{config['main_class']}{config['file_ext']}"
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_name)
    else:
        # Для других языков используем временный файл
        fd, file_path = tempfile.mkstemp(suffix=config['file_ext'])
        os.close(fd)
        temp_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
    
    # Записываем код в файл
    with open(file_path, 'w') as f:
        f.write(code)
    
    return file_path, file_name, temp_dir

def compile_code(file_path: str, language: str) -> None:
    """
    Компилирует код, если это необходимо (для языков типа C++, Java)
    
    Args:
        file_path: Путь к файлу с исходным кодом
        language: Язык программирования
    
    Raises:
        CompilationError: Если компиляция завершилась с ошибкой
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config or not config['compile_cmd']:
        return  # Компиляция не требуется (Python, JavaScript)
    
    cmd = [c.format(file=file_path, dir=os.path.dirname(file_path)) for c in config['compile_cmd']]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate(timeout=30)
        
        if process.returncode != 0:
            raise CompilationError(f"Ошибка компиляции ({language}):\n{stderr}")
    except subprocess.TimeoutExpired:
        process.kill()
        raise CompilationError(f"Компиляция превысила лимит времени (30 секунд)")

def limit_resources(max_memory_bytes: int) -> None:
    """
    Ограничивает ресурсы для дочернего процесса
    
    Args:
        max_memory_bytes: Максимальное количество памяти в байтах
    """
    # Ограничение использования памяти
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
    
    # Запрещаем создание новых процессов
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

def run_code_with_input(
    file_path: str, 
    language: str, 
    input_data: str = "",
    time_limit: float = DEFAULT_TIME_LIMIT,
    memory_limit: int = DEFAULT_MEMORY_LIMIT
) -> Dict[str, Any]:
    """
    Запускает код с заданными входными данными и ограничениями
    
    Args:
        file_path: Путь к файлу с исходным кодом
        language: Язык программирования
        input_data: Входные данные
        time_limit: Ограничение времени выполнения в секундах
        memory_limit: Ограничение памяти в байтах
    
    Returns:
        Словарь с результатами выполнения:
        {
            'status': 'success' или 'error',
            'output': строка вывода (при успехе) или сообщение об ошибке,
            'execution_time': время выполнения в секундах,
            'memory_used': использованная память в байтах (приблизительно)
        }
    """
    try:
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            return {
                'status': 'error',
                'output': f"Неподдерживаемый язык: {language}"
            }
        
        # Компилируем код, если требуется
        if config['compile_cmd']:
            compile_code(file_path, language)
        
        # Подготавливаем команду запуска
        cmd = [c.format(file=file_path, dir=os.path.dirname(file_path)) for c in config['run_cmd']]
        
        # Запускаем процесс
        start_time = time.time()
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            preexec_fn=lambda: limit_resources(memory_limit)
        )
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=time_limit)
            execution_time = time.time() - start_time
            
            # Ограничиваем размер вывода
            if len(stdout) > MAX_OUTPUT_LENGTH:
                stdout = stdout[:MAX_OUTPUT_LENGTH] + "\n... (вывод обрезан)"
            
            if process.returncode != 0:
                return {
                    'status': 'error',
                    'output': f"Ошибка выполнения (код {process.returncode}):\n{stderr}",
                    'execution_time': execution_time
                }
            
            # Если есть вывод ошибок, но код возврата 0, добавляем их к stdout
            if stderr and process.returncode == 0:
                full_output = stdout
                if stderr.strip():
                    full_output += "\n--- Stderr ---\n" + stderr
                
                return {
                    'status': 'success',
                    'output': full_output,
                    'execution_time': execution_time
                }
            
            return {
                'status': 'success',
                'output': stdout,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            # Если процесс не завершился вовремя, убиваем его
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.kill()
            
            return {
                'status': 'error',
                'output': f"Превышено ограничение времени выполнения ({time_limit} сек)",
                'execution_time': time_limit
            }
    
    except CompilationError as e:
        return {
            'status': 'error',
            'output': str(e)
        }
    except Exception as e:
        return {
            'status': 'error',
            'output': f"Внутренняя ошибка: {str(e)}"
        }

def check_solution(
    code: str,
    language: str,
    test_cases: List[Dict[str, str]],
    time_limit: float = DEFAULT_TIME_LIMIT,
    memory_limit: int = DEFAULT_MEMORY_LIMIT
) -> Dict[str, Any]:
    """
    Проверяет решение на наборе тестовых случаев
    
    Args:
        code: Исходный код
        language: Язык программирования
        test_cases: Список тестовых случаев вида [{'input': '...', 'expected': '...'}]
        time_limit: Ограничение времени выполнения в секундах
        memory_limit: Ограничение памяти в байтах
    
    Returns:
        Словарь с результатами проверки:
        {
            'status': 'success' или 'error',
            'all_passed': True/False если все тесты пройдены,
            'passed_count': количество пройденных тестов,
            'total_count': общее количество тестов,
            'test_results': список результатов по каждому тесту,
            'error': сообщение об ошибке (если есть)
        }
    """
    try:
        # Создаем временный файл с кодом
        file_path, _, _ = create_temp_file(code, language)
        
        # Компилируем код, если требуется
        try:
            if LANGUAGE_CONFIG[language]['compile_cmd']:
                compile_code(file_path, language)
        except CompilationError as e:
            return {
                'status': 'error',
                'error': str(e),
                'all_passed': False,
                'passed_count': 0,
                'total_count': len(test_cases),
                'test_results': []
            }
        
        # Проверяем каждый тестовый случай
        test_results = []
        passed_count = 0
        
        for i, test_case in enumerate(test_cases):
            input_data = test_case.get('input', '')
            expected_output = test_case.get('expected', '').strip()
            
            # Запускаем код с текущим входным набором
            result = run_code_with_input(
                file_path, 
                language, 
                input_data, 
                time_limit, 
                memory_limit
            )
            
            if result['status'] == 'success':
                actual_output = result['output'].strip()
                is_passed = actual_output == expected_output
                
                if is_passed:
                    passed_count += 1
                
                test_results.append({
                    'test_number': i + 1,
                    'input': input_data,
                    'expected': expected_output,
                    'actual': actual_output,
                    'execution_time': result.get('execution_time', 0),
                    'passed': is_passed
                })
            else:
                # Если произошла ошибка выполнения, помечаем тест как не пройденный
                test_results.append({
                    'test_number': i + 1,
                    'input': input_data,
                    'expected': expected_output,
                    'actual': result['output'],
                    'execution_time': result.get('execution_time', 0),
                    'passed': False,
                    'error': True
                })
        
        # Очищаем временный файл
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            'status': 'success',
            'all_passed': passed_count == len(test_cases),
            'passed_count': passed_count,
            'total_count': len(test_cases),
            'test_results': test_results
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'error': f"Внутренняя ошибка при проверке решения: {str(e)}",
            'all_passed': False,
            'passed_count': 0,
            'total_count': len(test_cases),
            'test_results': []
        }

def format_code(code: str, language: str) -> Dict[str, Any]:
    """
    Форматирует код с использованием соответствующих инструментов
    
    Args:
        code: Исходный код
        language: Язык программирования
    
    Returns:
        Словарь с результатами форматирования:
        {
            'status': 'success' или 'error',
            'formatted_code': отформатированный код (при успехе),
            'error': сообщение об ошибке (при неудаче)
        }
    """
    try:
        config = LANGUAGE_CONFIG.get(language)
        if not config or not config.get('format_cmd'):
            # Если нет команды форматирования, возвращаем исходный код
            return {
                'status': 'success',
                'formatted_code': code
            }
        
        # Создаем временный файл с кодом
        file_path, _, _ = create_temp_file(code, language)
        
        # Форматируем код
        cmd = [c.format(file=file_path, dir=os.path.dirname(file_path)) for c in config['format_cmd']]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate(timeout=10)
            
            # Некоторые форматеры выводят сообщения в stderr, но это не обязательно означает ошибку
            if process.returncode != 0:
                return {
                    'status': 'error',
                    'error': f"Ошибка форматирования ({language}):\n{stderr}"
                }
            
            # Читаем отформатированный код
            with open(file_path, 'r') as f:
                formatted_code = f.read()
            
            # Очищаем временный файл
            try:
                os.remove(file_path)
            except:
                pass
            
            return {
                'status': 'success',
                'formatted_code': formatted_code
            }
        
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'status': 'error',
                'error': "Форматирование превысило лимит времени (10 секунд)"
            }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': f"Внутренняя ошибка при форматировании: {str(e)}"
        }