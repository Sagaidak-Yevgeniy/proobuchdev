from django.contrib import admin

from .models import Widget, DashboardLayout, WidgetDataCache


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'widget_type', 'size', 'is_active', 'created_at')
    list_filter = ('widget_type', 'size', 'is_active', 'created_at')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'animation_speed', 'updated_at')
    list_filter = ('theme', 'animation_speed', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)


@admin.register(WidgetDataCache)
class WidgetDataCacheAdmin(admin.ModelAdmin):
    list_display = ('widget', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('widget__title', 'widget__user__username')
    readonly_fields = ('last_updated',)