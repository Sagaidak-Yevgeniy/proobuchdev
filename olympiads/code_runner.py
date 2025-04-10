import os
import tempfile
import subprocess
import time
import resource
import signal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Ограничения по умолчанию
DEFAULT_TIME_LIMIT = 5  # секунд
DEFAULT_MEMORY_LIMIT = 512  # МБ

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    'python': {
        'extension': '.py',
        'compile_cmd': None,
        'run_cmd': 'python3 {filename}',
    },
    'cpp': {
        'extension': '.cpp',
        'compile_cmd': 'g++ -std=c++17 -O2 -o {executable} {filename}',
        'run_cmd': './{executable}',
    },
    'java': {
        'extension': '.java',
        'compile_cmd': 'javac {filename}',
        'run_cmd': 'java -cp {directory} Main',
    },
    'javascript': {
        'extension': '.js',
        'compile_cmd': None,
        'run_cmd': 'node {filename}',
    },
}


class ExecutionTimeLimitExceeded(Exception):
    """Превышено ограничение по времени выполнения"""
    pass


class ExecutionMemoryLimitExceeded(Exception):
    """Превышено ограничение по памяти"""
    pass


class ExecutionRuntimeError(Exception):
    """Ошибка выполнения"""
    pass


class CompilationError(Exception):
    """Ошибка компиляции"""
    pass


def timeout_handler(signum, frame):
    """Обработчик сигнала для ограничения времени выполнения"""
    raise ExecutionTimeLimitExceeded("Превышено ограничение по времени выполнения")


def compile_code(code, language):
    """
    Компилирует исходный код, если требуется для языка.
    
    Args:
        code (str): Исходный код
        language (str): Язык программирования
        
    Returns:
        tuple: (temp_dir, filename, executable) - директория, имя файла и исполняемый файл
        
    Raises:
        CompilationError: Если компиляция завершилась с ошибкой
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Неподдерживаемый язык программирования: {language}")
    
    lang_config = SUPPORTED_LANGUAGES[language]
    extension = lang_config['extension']
    compile_cmd = lang_config['compile_cmd']
    
    # Создаем временную директорию для файлов
    temp_dir = tempfile.mkdtemp()
    
    # Для Java создаем файл Main.java
    if language == 'java':
        filename = os.path.join(temp_dir, 'Main' + extension)
    else:
        filename = os.path.join(temp_dir, 'solution' + extension)
    
    # Создаем файл с исходным кодом
    with open(filename, 'w') as f:
        f.write(code)
    
    # Если компиляция не требуется, просто возвращаем имя файла
    if compile_cmd is None:
        return temp_dir, filename, filename
    
    # Для компилируемых языков
    if language == 'cpp':
        executable = os.path.join(temp_dir, 'solution')
    elif language == 'java':
        executable = os.path.join(temp_dir, 'Main.class')
    else:
        executable = filename
    
    # Компилируем код
    cmd = compile_cmd.format(
        filename=filename,
        executable=executable,
        directory=temp_dir
    )
    
    try:
        process = subprocess.run(
            cmd,
            shell=True,
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=30  # Ограничиваем время компиляции 30 секундами
        )
        
        if process.returncode != 0:
            raise CompilationError(
                f"Ошибка компиляции:\n{process.stderr or process.stdout}"
            )
        
        return temp_dir, filename, executable
    
    except subprocess.TimeoutExpired:
        raise CompilationError("Превышено время компиляции")


def run_code_with_input(executable, language, input_data, time_limit=DEFAULT_TIME_LIMIT, memory_limit=DEFAULT_MEMORY_LIMIT):
    """
    Выполняет программу с заданными входными данными и ограничениями.
    
    Args:
        executable: Путь к исполняемому файлу или скрипту
        language: Язык программирования
        input_data: Входные данные для программы
        time_limit: Ограничение по времени в секундах
        memory_limit: Ограничение по памяти в МБ
        
    Returns:
        tuple: (output, execution_time, memory_usage) - вывод, время выполнения, использованная память
        
    Raises:
        ExecutionTimeLimitExceeded: Если превышено ограничение по времени
        ExecutionMemoryLimitExceeded: Если превышено ограничение по памяти
        ExecutionRuntimeError: Если произошла ошибка во время выполнения
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Неподдерживаемый язык программирования: {language}")
    
    lang_config = SUPPORTED_LANGUAGES[language]
    run_cmd = lang_config['run_cmd']
    
    if language == 'java':
        directory = os.path.dirname(executable)
    else:
        directory = os.path.dirname(executable)
    
    # Формируем команду для запуска
    cmd = run_cmd.format(
        filename=executable,
        executable=executable,
        directory=directory
    )
    
    # Создаем временный файл для входных данных
    input_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    input_file.write(input_data)
    input_file.close()
    
    # Устанавливаем обработчик для ограничения времени выполнения
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(time_limit)
    
    start_time = time.time()
    max_memory = 0
    
    try:
        # Запускаем процесс
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=directory,
            stdin=open(input_file.name, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=lambda: resource.setrlimit(
                resource.RLIMIT_AS, 
                (memory_limit * 1024 * 1024, memory_limit * 1024 * 1024)
            )
        )
        
        # Отслеживаем использование памяти
        while process.poll() is None:
            try:
                # Получаем информацию о процессе
                with open(f'/proc/{process.pid}/status', 'r') as f:
                    stats = f.read()
                    
                # Ищем строку с VmPeak (максимальное использование памяти)
                for line in stats.splitlines():
                    if line.startswith('VmPeak:'):
                        kb = int(line.split()[1])
                        mb = kb / 1024
                        max_memory = max(max_memory, mb)
                        
                        # Проверяем превышение лимита памяти
                        if mb > memory_limit:
                            process.kill()
                            raise ExecutionMemoryLimitExceeded(
                                f"Превышено ограничение по памяти: {mb:.2f} МБ > {memory_limit} МБ"
                            )
                
                time.sleep(0.1)
                
            except (FileNotFoundError, IOError, ProcessLookupError):
                # Процесс мог уже завершиться
                break
        
        stdout, stderr = process.communicate()
        
        # Отключаем таймер
        signal.alarm(0)
        
        execution_time = time.time() - start_time
        
        if execution_time > time_limit:
            raise ExecutionTimeLimitExceeded(
                f"Превышено ограничение по времени: {execution_time:.2f} сек > {time_limit} сек"
            )
        
        if process.returncode != 0:
            raise ExecutionRuntimeError(f"Ошибка выполнения:\n{stderr}")
        
        return stdout.strip(), execution_time, max_memory
    
    except (OSError, subprocess.SubprocessError) as e:
        signal.alarm(0)
        raise ExecutionRuntimeError(f"Ошибка запуска процесса: {str(e)}")
    
    finally:
        signal.alarm(0)
        # Удаляем временный файл входных данных
        os.unlink(input_file.name)


def check_solution(code, language, test_cases, time_limit=DEFAULT_TIME_LIMIT, memory_limit=DEFAULT_MEMORY_LIMIT):
    """
    Проверяет решение по набору тестовых случаев.
    
    Args:
        code (str): Исходный код решения
        language (str): Язык программирования
        test_cases (list): Список тестовых случаев вида [(input, expected_output), ...]
        time_limit (int): Ограничение по времени в секундах
        memory_limit (int): Ограничение по памяти в МБ
        
    Returns:
        tuple: (results, passed_count, total_count) - результаты, количество пройденных тестов, общее количество тестов
        где results - список кортежей (test_case_id, passed, output, expected, error, time, memory)
    """
    results = []
    passed_count = 0
    total_count = len(test_cases)
    
    try:
        # Компилируем код если нужно
        temp_dir, filename, executable = compile_code(code, language)
        
        # Выполняем проверку на каждом тестовом случае
        for i, (input_data, expected_output) in enumerate(test_cases):
            try:
                output, execution_time, memory_usage = run_code_with_input(
                    executable, language, input_data, time_limit, memory_limit
                )
                
                # Нормализуем вывод для сравнения (убираем лишние пробелы и переводы строк)
                normalized_output = output.strip()
                normalized_expected = expected_output.strip()
                
                # Сравниваем результаты
                passed = normalized_output == normalized_expected
                if passed:
                    passed_count += 1
                
                results.append({
                    'test_case_id': i + 1,
                    'passed': passed,
                    'output': output,
                    'expected': expected_output,
                    'error': None,
                    'execution_time': execution_time,
                    'memory_usage': memory_usage
                })
                
            except (ExecutionTimeLimitExceeded, ExecutionMemoryLimitExceeded, ExecutionRuntimeError) as e:
                results.append({
                    'test_case_id': i + 1,
                    'passed': False,
                    'output': None,
                    'expected': expected_output,
                    'error': str(e),
                    'execution_time': 0,
                    'memory_usage': 0
                })
        
    except CompilationError as e:
        # Все тестовые случаи не проходят при ошибке компиляции
        for i in range(total_count):
            results.append({
                'test_case_id': i + 1,
                'passed': False,
                'output': None,
                'expected': test_cases[i][1],
                'error': str(e),
                'execution_time': 0,
                'memory_usage': 0
            })
    
    finally:
        # Удаляем временную директорию с кодом
        import shutil
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
    
    return results, passed_count, total_count