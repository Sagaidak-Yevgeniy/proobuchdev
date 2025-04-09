from django.contrib import admin
from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'is_high_priority', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_high_priority', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'content_type')
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'message')
        }),
        ('Настройки', {
            'fields': ('notification_type', 'is_read', 'is_high_priority', 'url')
        }),
        ('Связанный объект', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} уведомлений отмечено как прочитанные.')
    mark_as_read.short_description = "Отметить как прочитанные"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} уведомлений отмечено как непрочитанные.')
    mark_as_unread.short_description = "Отметить как непрочитанные"


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_all', 'notify_only_high_priority', 'email_notifications', 'updated_at')
    list_filter = ('receive_all', 'notify_only_high_priority', 'email_notifications', 'email_digest')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Общие настройки', {
            'fields': ('receive_all', 'notify_only_high_priority')
        }),
        ('Настройки по типам', {
            'fields': ('receive_achievement', 'receive_course', 'receive_lesson', 'receive_assignment', 'receive_message')
        }),
        ('Email-уведомления', {
            'fields': ('email_notifications', 'email_digest')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )