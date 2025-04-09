#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

from django.db import connection

def check_table_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name=%s', [table_name])
        columns = [row[0] for row in cursor.fetchall()]
        return columns

if __name__ == '__main__':
    table_name = 'notifications_notificationsettings'
    columns = check_table_columns(table_name)
    print(f"Columns in {table_name}:")
    for column in columns:
        print(f"- {column}")