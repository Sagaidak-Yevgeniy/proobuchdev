"""
Модуль для запуска и проверки программного кода для олимпиадных заданий
"""

import os
import subprocess
import tempfile
import uuid
import time
import json
from django.conf import settings

# Максимальное время выполнения кода (в секундах)
DEFAULT_TIMEOUT = 5

# Максимальный объем памяти (в мегабайтах)
DEFAULT_MEMORY_LIMIT = 100

# Поддерживаемые языки программирования и их компиляторы/интерпретаторы
SUPPORTED_LANGUAGES = {
    'python': {
        'extension': 'py',
        'compile': None,
        'run': ['python', '{file}'],
        'version_cmd': ['python', '--version'],
        'name': 'Python',
    },
    'javascript': {
        'extension': 'js',
        'compile': None,
        'run': ['node', '{file}'],
        'version_cmd': ['node', '--version'],
        'name': 'JavaScript (Node.js)',
    },
    'java': {
        'extension': 'java',
        'compile': ['javac', '{file}'],
        'run': ['java', '-cp', '{dir}', 'Main'],
        'version_cmd': ['java', '--version'],
        'name': 'Java',
        'main_class': 'Main',
    },
    'cpp': {
        'extension': 'cpp',
        'compile': ['g++', '-std=c++17', '{file}', '-o', '{dir}/a.out'],
        'run': ['{dir}/a.out'],
        'version_cmd': ['g++', '--version'],
        'name': 'C++',
    },
    'csharp': {
        'extension': 'cs',
        'compile': ['csc', '{file}', '-out:{dir}/program.exe'],
        'run': ['mono', '{dir}/program.exe'],
        'version_cmd': ['csc', '--version'],
        'name': 'C#',
    },
    'ruby': {
        'extension': 'rb',
        'compile': None,
        'run': ['ruby', '{file}'],
        'version_cmd': ['ruby', '--version'],
        'name': 'Ruby',
    },
    'php': {
        'extension': 'php',
        'compile': None,
        'run': ['php', '{file}'],
        'version_cmd': ['php', '--version'],
        'name': 'PHP',
    },
}

# Рабочая директория для временных файлов
WORK_DIR = os.path.join(settings.BASE_DIR, 'tmp', 'code_runner')
os.makedirs(WORK_DIR, exist_ok=True)

def get_language_config(language):
    """
    Получает конфигурацию для указанного языка программирования
    
    Args:
        language (str): Идентификатор языка программирования
    
    Returns:
        dict: Конфигурация языка или None, если язык не поддерживается
    """
    language = language.lower()
    return SUPPORTED_LANGUAGES.get(language)

def run_code(code, language, input_data=None, timeout=DEFAULT_TIMEOUT, memory_limit=DEFAULT_MEMORY_LIMIT):
    """
    Запускает код на указанном языке программирования
    
    Args:
        code (str): Код для запуска
        language (str): Язык программирования
        input_data (str, optional): Входные данные для программы
        timeout (int, optional): Максимальное время выполнения в секундах
        memory_limit (int, optional): Максимальный объем памяти в мегабайтах
    
    Returns:
        dict: Результат выполнения кода
    """
    # Получаем конфигурацию языка
    lang_config = get_language_config(language)
    if not lang_config:
        return {
            'status': 'error',
            'error': f'Язык "{language}" не поддерживается'
        }
    
    # Создаем временный файл для кода
    uid = uuid.uuid4().hex
    temp_dir = os.path.join(WORK_DIR, uid)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Формируем имя файла
        file_name = f"main.{lang_config['extension']}"
        file_path = os.path.join(temp_dir, file_name)
        
        # Если это Java, нужно использовать имя класса Main
        if language == 'java':
            code = code.replace('public class', 'class')
            code = f"public class {lang_config['main_class']} {{\n{code.strip()}\n}}"
        
        # Записываем код во временный файл
        with open(file_path, 'w') as f:
            f.write(code)
        
        # Компилируем код, если нужно
        if lang_config['compile']:
            compile_cmd = [
                cmd.format(file=file_path, dir=temp_dir)
                for cmd in lang_config['compile']
            ]
            
            compile_process = subprocess.run(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
            
            if compile_process.returncode != 0:
                return {
                    'status': 'error',
                    'error': f'Ошибка компиляции:\n{compile_process.stderr}'
                }
        
        # Запускаем программу
        run_cmd = [
            cmd.format(file=file_path, dir=temp_dir)
            for cmd in lang_config['run']
        ]
        
        # Если есть входные данные, записываем их во временный файл
        input_file = None
        if input_data:
            input_file = os.path.join(temp_dir, 'input.txt')
            with open(input_file, 'w') as f:
                f.write(input_data)
        
        # Запускаем процесс
        start_time = time.time()
        
        with open(input_file, 'r') if input_file else None as inp:
            try:
                process = subprocess.run(
                    run_cmd,
                    stdin=inp,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    text=True
                )
                
                execution_time = time.time() - start_time
                
                if process.returncode != 0:
                    return {
                        'status': 'error',
                        'error': f'Ошибка выполнения:\n{process.stderr}',
                        'output': process.stdout,
                        'execution_time': execution_time
                    }
                
                return {
                    'status': 'success',
                    'output': process.stdout,
                    'execution_time': execution_time,
                    'memory_usage': 0  # В простой версии не измеряем использование памяти
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'status': 'error',
                    'error': f'Превышено ограничение по времени ({timeout} сек)'
                }
            
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Произошла ошибка: {str(e)}'
        }
    
    finally:
        # Удаляем временные файлы
        cleanup_temp_files(temp_dir)

def run_test_case(code, language, test_case, timeout=DEFAULT_TIMEOUT, memory_limit=DEFAULT_MEMORY_LIMIT):
    """
    Запускает код на указанном языке программирования с тестовым случаем
    
    Args:
        code (str): Код для запуска
        language (str): Язык программирования
        test_case (dict): Тестовый случай с входными данными и ожидаемым результатом
        timeout (int, optional): Максимальное время выполнения в секундах
        memory_limit (int, optional): Максимальный объем памяти в мегабайтах
    
    Returns:
        dict: Результат прохождения теста
    """
    # Получаем входные данные и ожидаемый результат
    input_data = test_case.get('input_data', '')
    expected_output = test_case.get('expected_output', '').strip()
    
    # Запускаем код
    result = run_code(code, language, input_data, timeout, memory_limit)
    
    # Если произошла ошибка, возвращаем её
    if result['status'] == 'error':
        return {
            'status': 'error',
            'error': result['error'],
            'passed': False,
            'test_id': test_case.get('id')
        }
    
    # Получаем выходные данные
    actual_output = result['output'].strip()
    
    # Сравниваем выходные данные с ожидаемым результатом
    passed = actual_output == expected_output
    
    return {
        'status': 'success',
        'passed': passed,
        'expected_output': expected_output,
        'actual_output': actual_output,
        'execution_time': result['execution_time'],
        'memory_usage': result.get('memory_usage', 0),
        'test_id': test_case.get('id')
    }

def format_code(code, language):
    """
    Форматирует код на указанном языке программирования
    
    Args:
        code (str): Код для форматирования
        language (str): Язык программирования
    
    Returns:
        dict: Результат форматирования
    """
    # Получаем конфигурацию языка
    lang_config = get_language_config(language)
    if not lang_config:
        return {
            'status': 'error',
            'error': f'Язык "{language}" не поддерживается'
        }
    
    # Создаем временный файл для кода
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Формируем имя файла
            file_name = f"main.{lang_config['extension']}"
            file_path = os.path.join(temp_dir, file_name)
            
            # Записываем код во временный файл
            with open(file_path, 'w') as f:
                f.write(code)
            
            # Форматируем код в зависимости от языка
            if language == 'python':
                # Используем black для Python
                try:
                    subprocess.run(
                        ['black', '-q', file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                        text=True
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Если black не установлен, пропускаем форматирование
                    pass
                
            elif language == 'javascript':
                # Используем prettier для JavaScript
                try:
                    subprocess.run(
                        ['prettier', '--write', file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                        text=True
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Если prettier не установлен, пропускаем форматирование
                    pass
                
            elif language in ['java', 'cpp', 'csharp']:
                # Используем clang-format для C-подобных языков
                try:
                    subprocess.run(
                        ['clang-format', '-i', file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                        text=True
                    )
                except (subprocess.SubprocessError, FileNotFoundError):
                    # Если clang-format не установлен, пропускаем форматирование
                    pass
            
            # Считываем отформатированный код
            with open(file_path, 'r') as f:
                formatted_code = f.read()
            
            return {
                'status': 'success',
                'formatted_code': formatted_code
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Произошла ошибка при форматировании: {str(e)}'
            }

def cleanup_temp_files(directory):
    """
    Удаляет временные файлы
    
    Args:
        directory (str): Путь к директории с временными файлами
    """
    try:
        # Рекурсивно удаляем все файлы в директории
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        
        # Удаляем саму директорию
        os.rmdir(directory)
    except Exception as e:
        print(f"Ошибка при удалении временных файлов: {e}")

def get_available_languages():
    """
    Возвращает список доступных языков программирования
    
    Returns:
        list: Список доступных языков
    """
    languages = []
    
    for lang_id, config in SUPPORTED_LANGUAGES.items():
        # Проверяем, установлен ли компилятор/интерпретатор
        try:
            subprocess.run(
                config['version_cmd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            
            languages.append({
                'id': lang_id,
                'name': config['name'],
                'available': True
            })
        except (subprocess.SubprocessError, FileNotFoundError):
            languages.append({
                'id': lang_id,
                'name': config['name'],
                'available': False
            })
    
    return languages