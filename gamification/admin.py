from django.contrib import admin
from .models import Achievement, UserAchievement, Badge, UserBadge, PointsHistory


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'difficulty', 'points', 'is_hidden')
    list_filter = ('type', 'difficulty', 'is_hidden')
    search_fields = ('name', 'description')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'earned_at')
    list_filter = ('achievement__type', 'earned_at')
    search_fields = ('user__username', 'achievement__name')
    date_hierarchy = 'earned_at'


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'required_points')
    search_fields = ('name', 'description')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('earned_at',)
    search_fields = ('user__username', 'badge__name')
    date_hierarchy = 'earned_at'


@admin.register(PointsHistory)
class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'action', 'description', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'created_at'