from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .code_runner import format_code as format_code_function

@csrf_exempt
@require_POST
def format_code_view(request):
    """Форматирует код с помощью соответствующих инструментов"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        # Используем функцию из code_runner для форматирования
        result = format_code_function(code, language)
        
        if result['status'] == 'success':
            return JsonResponse({
                'status': 'success',
                'formatted_code': result['formatted_code']
            })
        else:
            return JsonResponse({
                'status': 'error',
                'error': result['error']
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })