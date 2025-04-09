from django.core.management.base import BaseCommand
from olympiads.models import Problem, TestCase
import random

class Command(BaseCommand):
    help = 'Создает тестовые случаи для задач олимпиады'

    def add_arguments(self, parser):
        parser.add_argument('problem_id', type=int, help='ID задачи олимпиады')
        parser.add_argument('--count', type=int, default=5, help='Количество тестовых случаев')

    def handle(self, *args, **options):
        problem_id = options['problem_id']
        count = options['count']

        try:
            problem = Problem.objects.get(pk=problem_id)
        except Problem.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Задача с ID {problem_id} не найдена!'))
            return

        # Удаляем существующие тестовые случаи для задачи
        TestCase.objects.filter(problem=problem).delete()

        # Примеры тестовых случаев для разных типов задач
        test_cases = []

        # Простой пример: сложение двух чисел
        if "сложение" in problem.title.lower() or "сумма" in problem.title.lower():
            for i in range(count):
                a = random.randint(1, 100)
                b = random.randint(1, 100)
                input_data = f"{a} {b}"
                expected_output = str(a + b)
                weight = 1 if i < count // 2 else 2  # более сложные тесты имеют больший вес
                is_example = (i == 0)  # первый тест будет примером
                test_cases.append((input_data, expected_output, is_example, weight, i + 1))

        # Пример: поиск максимального числа
        elif "максимум" in problem.title.lower() or "наибольшее" in problem.title.lower():
            for i in range(count):
                nums_count = random.randint(3, 10)
                nums = [random.randint(-100, 100) for _ in range(nums_count)]
                input_data = f"{nums_count}\n" + " ".join(map(str, nums))
                expected_output = str(max(nums))
                weight = 1 if nums_count < 5 else 2
                is_example = (i == 0)
                test_cases.append((input_data, expected_output, is_example, weight, i + 1))

        # Пример: проверка на простое число
        elif "простое" in problem.title.lower() or "prime" in problem.title.lower():
            for i in range(count):
                if i == 0:  # пример
                    num = 7  # простое число
                elif i == 1:
                    num = 4  # составное число
                else:
                    num = random.randint(2, 1000)
                input_data = str(num)
                
                # Проверка на простое число
                is_prime = True
                if num < 2:
                    is_prime = False
                else:
                    for j in range(2, int(num**0.5) + 1):
                        if num % j == 0:
                            is_prime = False
                            break
                            
                expected_output = "YES" if is_prime else "NO"
                weight = 1 if num < 100 else 2
                is_example = (i < 2)  # первые два теста будут примерами
                test_cases.append((input_data, expected_output, is_example, weight, i + 1))

        # Общий случай - создаем базовые тестовые случаи
        else:
            test_cases = [
                ("10", "10", True, 1, 1),
                ("5 7", "12", True, 1, 2),
                ("100 200", "300", False, 2, 3),
                ("15 -5", "10", False, 2, 4),
                ("1000 1000", "2000", False, 3, 5)
            ]

        # Создаем тестовые случаи
        for input_data, expected_output, is_example, weight, order in test_cases:
            TestCase.objects.create(
                problem=problem,
                input_data=input_data,
                expected_output=expected_output,
                is_example=is_example,
                weight=weight,
                order=order
            )

        self.stdout.write(self.style.SUCCESS(f'Создано {len(test_cases)} тестовых случаев для задачи "{problem.title}"'))