from django.contrib import admin
from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'is_high_priority', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_high_priority', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Состояние', {
            'fields': ('is_read', 'is_high_priority')
        }),
        ('Ссылки', {
            'fields': ('url', 'content_type', 'object_id')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Оптимизация запросов с select_related для связанных моделей"""
        return super().get_queryset(request).select_related('user', 'content_type')
    
    def get_user_display(self, obj):
        """Отображает имя пользователя"""
        return obj.user.get_full_name() or obj.user.username
    get_user_display.short_description = 'Пользователь'
    
    def get_type_display(self, obj):
        """Отображает тип уведомления с цветным индикатором"""
        return obj.get_notification_type_display()
    get_type_display.short_description = 'Тип'


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_all', 'notify_only_high_priority', 'email_notifications', 'updated_at')
    list_filter = ('receive_all', 'notify_only_high_priority', 'email_notifications', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Общие настройки', {
            'fields': ('receive_all', 'notify_only_high_priority')
        }),
        ('Типы уведомлений', {
            'fields': ('receive_achievement', 'receive_course', 'receive_lesson', 'receive_assignment', 'receive_message')
        }),
        ('Email-уведомления', {
            'fields': ('email_notifications', 'email_digest')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Оптимизация запросов с select_related для связанных моделей"""
        return super().get_queryset(request).select_related('user')