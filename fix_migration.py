#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educational_platform.settings')
django.setup()

from django.db import connection

def fix_migrations():
    with connection.cursor() as cursor:
        print("Deleting problematic migration record...")
        cursor.execute("DELETE FROM django_migrations WHERE app='notifications' AND name='0003_notificationsettings_push_notifications'")
        print("Setting default value for push_notifications field...")
        cursor.execute("UPDATE notifications_notificationsettings SET push_notifications=false WHERE push_notifications IS NULL")
        print("Migration fixed!")

if __name__ == '__main__':
    fix_migrations()