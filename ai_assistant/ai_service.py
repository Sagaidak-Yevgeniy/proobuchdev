import os
import json
from openai import OpenAI
from django.conf import settings

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user

class AIAssistant:
    """Класс для работы с OpenAI API"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o"
    
    def is_available(self):
        """Проверяет доступность API"""
        return self.api_key is not None and self.client is not None
    
    def generate_response(self, user_message, context=None, max_tokens=500):
        """Генерирует ответ на сообщение пользователя с учетом контекста"""
        if not self.is_available():
            return {
                "success": False,
                "message": "API ключ не настроен. Обратитесь к администратору."
            }
        
        try:
            # Формируем сообщения для запроса
            messages = []
            
            # Системный промпт для определения роли ассистента
            system_prompt = """Ты - AI-ассистент образовательной платформы по программированию.
            Твоя задача помогать студентам с их вопросами по программированию, разъяснять сложные концепции и давать подсказки в решении заданий.
            Не давай готовых решений заданий, а только подсказки и направления.
            Отвечай кратко, понятно и информативно. Используй примеры кода, где это уместно.
            Твои ответы должны быть на русском языке."""
            
            messages.append({"role": "system", "content": system_prompt})
            
            # Если есть контекст, добавляем его в запрос
            if context:
                if "course_title" in context and "lesson_title" in context:
                    course_context = f"Контекст: Курс '{context['course_title']}', Урок '{context['lesson_title']}'"
                    messages.append({"role": "system", "content": course_context})
                
                if "lesson_content" in context:
                    content_context = f"Содержание урока: {context['lesson_content']}"
                    messages.append({"role": "system", "content": content_context})
                
                if "assignment" in context:
                    assignment_context = f"Задание: {context['assignment']}"
                    messages.append({"role": "system", "content": assignment_context})
            
            # Добавляем сообщение пользователя
            messages.append({"role": "user", "content": user_message})
            
            # Выполняем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )
            
            return {
                "success": True,
                "message": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при генерации ответа: {str(e)}"
            }
    
    def analyze_code(self, code, language="python", max_tokens=500):
        """Анализирует код и предлагает улучшения"""
        if not self.is_available():
            return {
                "success": False,
                "message": "API ключ не настроен. Обратитесь к администратору."
            }
        
        try:
            # Системный промпт для анализа кода
            system_prompt = f"""Проанализируй следующий код на {language} и предложи улучшения.
            Обрати внимание на:
            1. Синтаксические ошибки
            2. Логические ошибки
            3. Оптимизацию производительности
            4. Чистоту и читаемость кода
            5. Соответствие принятым практикам
            
            Формат ответа:
            - Общая оценка: (краткая оценка кода)
            - Обнаруженные проблемы: (список проблем)
            - Предложения по улучшению: (конкретные рекомендации)
            - Улучшенная версия: (если можно улучшить код, предложи улучшенную версию)"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": code}
            ]
            
            # Выполняем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            
            return {
                "success": True,
                "message": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при анализе кода: {str(e)}"
            }
    
    def generate_hint(self, assignment_text, user_code=None, max_tokens=300):
        """Генерирует подсказку для задания"""
        if not self.is_available():
            return {
                "success": False,
                "message": "API ключ не настроен. Обратитесь к администратору."
            }
        
        try:
            # Формируем контекст и промпт
            system_prompt = """Ты - помощник для образовательной платформы. 
            Твоя задача - дать подсказку по заданию, но не раскрывать полное решение.
            Дай направление для размышления и ключевые идеи, которые помогут студенту самостоятельно решить задачу.
            Краткость и ясность - ключевые принципы подсказки."""
            
            user_prompt = f"Задание: {assignment_text}"
            if user_code:
                user_prompt += f"\n\nМой текущий код:\n```\n{user_code}\n```\nПомоги мне понять, где я мог ошибиться или что мне стоит учесть."
            else:
                user_prompt += "\nПодскажи, как подойти к решению этого задания."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Выполняем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.5,
            )
            
            return {
                "success": True,
                "message": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при генерации подсказки: {str(e)}"
            }
    
    def generate_explanation(self, concept, max_tokens=500):
        """Генерирует объяснение для концепции или термина"""
        if not self.is_available():
            return {
                "success": False,
                "message": "API ключ не настроен. Обратитесь к администратору."
            }
        
        try:
            # Формируем контекст и промпт
            system_prompt = """Ты - эксперт в программировании и компьютерных науках.
            Твоя задача - объяснить сложные концепции простым и понятным языком.
            Используй примеры и аналогии, чтобы сделать объяснение наглядным.
            Ответ должен быть структурированным и лаконичным."""
            
            user_prompt = f"Объясни концепцию или термин: {concept}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Выполняем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            
            return {
                "success": True,
                "message": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при генерации объяснения: {str(e)}"
            }

# Создаем экземпляр класса для использования в приложении
ai_assistant = AIAssistant()