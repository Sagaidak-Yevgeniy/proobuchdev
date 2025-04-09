from django.contrib import admin
from .models import Notification, NotificationSettings, DeviceToken, NotificationChannel


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'importance', 'is_read', 'is_high_priority', 'created_at')
    list_filter = ('notification_type', 'importance', 'is_read', 'is_high_priority', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'message', 'notification_type', 'importance', 'is_high_priority')
        }),
        ('Статус', {
            'fields': ('is_read', 'url', 'icon')
        }),
        ('Связанный объект', {
            'fields': ('content_type', 'object_id')
        }),
        ('Дополнительная информация', {
            'fields': ('extra_data', 'created_at', 'updated_at')
        }),
    )


class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'receive_all', 'email_notifications', 'push_notifications', 'quiet_hours_enabled')
    list_filter = ('receive_all', 'notify_only_high_priority', 'email_notifications', 'push_notifications')
    search_fields = ('user__username',)
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Общие настройки', {
            'fields': ('receive_all', 'notify_only_high_priority')
        }),
        ('Типы уведомлений', {
            'fields': ('receive_achievement', 'receive_course', 'receive_lesson', 
                      'receive_assignment', 'receive_message', 'receive_system', 'receive_deadline')
        }),
        ('Email-уведомления', {
            'fields': ('email_notifications', 'email_digest')
        }),
        ('Push-уведомления', {
            'fields': ('push_notifications', 'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
        ('Каналы', {
            'fields': ('preferred_channels',)
        }),
    )
    filter_horizontal = ('preferred_channels',)


class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'device_name', 'is_active', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'device_name', 'token')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_token_preview(self, obj):
        return f"{obj.token[:10]}..." if obj.token else ""
    get_token_preview.short_description = "Токен (preview)"


class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_type', 'is_active')
    list_filter = ('channel_type', 'is_active')
    search_fields = ('name', 'description')


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationSettings, NotificationSettingsAdmin)
admin.site.register(DeviceToken, DeviceTokenAdmin)
admin.site.register(NotificationChannel, NotificationChannelAdmin)