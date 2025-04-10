#!/usr/bin/env python
"""
Скрипт для создания необходимых звуковых файлов для системы уведомлений.
Создает missing_sounds директорию со звуковыми файлами.
"""

import os
import base64
import sys


def create_notification_sounds():
    """
    Создает стандартные звуковые файлы для системы уведомлений,
    если они отсутствуют.
    """
    # Проверяем и создаем директорию для звуков
    static_dir = 'static'
    sounds_dir = os.path.join(static_dir, 'sounds')
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"✓ Создана директория: {static_dir}")
    
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
        print(f"✓ Создана директория: {sounds_dir}")
    
    # Закодированные в base64 минимальные MP3 файлы
    sound_files = {
        "success.mp3": "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAASAAAMTgAJCQkJFRUVFRUhISEhIS0tLS0tOTk5OTlFRUVFRUVRUVFRUV1dXV1daWlpaWl1dXV1dYGBgYGBjY2NjY2ZmZmZmaWlpaWlsbGxsbG9vb29vcXFxcXF0dHR0dHR3d3d3d3d6Ojo6Oj29vb29v////8AAAA5TEFNRTMuMTAwAZYAAAAALgAAA1AJLX9xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tAxAAAB9AJHxQAAJkZKnHrgUAH+hAQEHEDoOf/F8H3qAgIOD4Pg+/BAQf/xUKg/ZuDaP4ocVDnxUP4ocH3+KHPg+j+D4OL+KHBwf4qEWLvwQEBB////4Pg+D7+KAAA//ugxAAAMOAE1HlQAAYkNX3OPKAABDoJgkCQJAkCQJDJIBYJCwj3UCT5D5cwIKxEIEgSBIEgSBIZJALBIWEe6gSfIfLmBBWIBHgMGUB/b6HHvRWiQaBMFNNVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV",
        "error.mp3": "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAASAAAPkgAJCQkJFRUVFRUhISEhIS0tLS0tOTk5OTlFRUVFRUVRUVFRUV1dXV1daWlpaWl1dXV1dYGBgYGBjY2NjY2ZmZmZmaWlpaWlsbGxsbG9vb29vcXFxcXF0dHR0dHR3d3d3d3d6Ojo6Oj29vb29v////8AAAA5TEFNRTMuMTAwAZYAAAAALgAAA1QIJl+fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tAxAAAB74JHFQAAJkOI+jLkQAHwoKCggwMAJn/7giEQm//wxGMoH///4YnEOBs/xjT/8/H/DP/8PxvD8ED//+GAM2f/0AAA//ugxAAAMLAEtHkQAAYkJ4XOPKAAR7hYsgkV47gMMRCAR4kIsB3IaC1YMiPVCGQS3DQWrBkR6oQCLAgQCHEQYD2Ae4D3Ae4EAgQIEAgREGA90LuhdyLkD3Ae4D3AfxAgfBDiIMB7gPcB7gPcCBAgQIBAiIMB7oXdC7kXIA//4XRVZxCCMj2RrI9mnTp06dOnnTp06dOm",
        "warning.mp3": "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAASAAALMgAJCQkJFRUVFRUhISEhIS0tLS0tOTk5OTlFRUVFRUVRUVFRUV1dXV1daWlpaWl1dXV1dYGBgYGBjY2NjY2ZmZmZmaWlpaWlsbGxsbG9vb29vcXFxcXF0dHR0dHR3d3d3d3d6Ojo6Oj29vb29v////8AAAA5TEFNRTMuMTAwAZYAAAAALgAAA1AHzFeBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tAxAAAB8YJH5wAAJkRP5XOKAAHAAIOD4Pg+D4Pg+DgQEBBw4hDzgQc8QB/8XB/4oDn/xfB9HB//FAc+D/i+DniAP/wQEHPioOD4Pg/igPg+//BAQ//IAAA//ugxAAAMAwEpDkAABYFgJNnIAAAgIgkGQRBgFgYDIN9rCoShIEgSDIMgsDAZBvtYVCUCQRCIVigUkQlEoEgSDIMgsDAZBvtYVCUCQRCIVigUkQlEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolEolA==",
        "info.mp3": "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAASAAAMTgAJCQkJFRUVFRUhISEhIS0tLS0tOTk5OTlFRUVFRUVRUVFRUV1dXV1daWlpaWl1dXV1dYGBgYGBjY2NjY2ZmZmZmaWlpaWlsbGxsbG9vb29vcXFxcXF0dHR0dHR3d3d3d3d6Ojo6Oj29vb29v////8AAAA5TEFNRTMuMTAwAZYAAAAALgAAA1AJLX9xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tAxAAAB9QJTFwAAJkZOoXrgUAHwQcHB8YP/BoP/+Cg/wfPg+//B8HzgQEHB/i+D8Hwf//Fg/wfP/xYPg+//F8+D4P/g//Dg+8H//BYPn//BAP/CAAA//ugxAAAMNQEpDkQABYOHEn49KAAUAIaHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yBs4aHHLBZMX8LrDRFhQR5vRq7yA==",
    }
    
    # Создаем файлы
    created_files = []
    for filename, base64_data in sound_files.items():
        file_path = os.path.join(sounds_dir, filename)
        
        if not os.path.exists(file_path):
            try:
                # Декодируем base64 и записываем в файл
                binary_data = base64.b64decode(base64_data)
                with open(file_path, 'wb') as f:
                    f.write(binary_data)
                created_files.append(filename)
                print(f"✓ Создан звуковой файл: {filename}")
            except Exception as e:
                print(f"✗ Ошибка при создании файла {filename}: {e}")
        else:
            print(f"⚠ Файл {filename} уже существует")
    
    # Проверяем, что все файлы созданы
    if len(created_files) == len(sound_files):
        print("\n✓ Все звуковые файлы для уведомлений успешно созданы")
    elif created_files:
        print(f"\n✓ Созданы звуковые файлы: {', '.join(created_files)}")
    else:
        print("\n⚠ Все звуковые файлы уже существуют")


if __name__ == '__main__':
    create_notification_sounds()
    print("\nПожалуйста, перезапустите сервер Django, чтобы применить изменения.")