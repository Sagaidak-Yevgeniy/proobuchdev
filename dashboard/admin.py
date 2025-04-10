from django.contrib import admin
from .models import Widget, DashboardLayout, WidgetDataCache
from .models_events import Event, EventParticipant
from .models_goals import StudentGoal, GoalStep


class WidgetDataCacheInline(admin.StackedInline):
    model = WidgetDataCache
    extra = 0


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'widget_type', 'size', 'is_active', 'created_at')
    list_filter = ('widget_type', 'size', 'is_active', 'created_at')
    search_fields = ('title', 'user__username')
    inlines = [WidgetDataCacheInline]


@admin.register(DashboardLayout)
class DashboardLayoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'animation_speed', 'updated_at')
    list_filter = ('theme', 'animation_speed', 'updated_at')
    search_fields = ('user__username',)


@admin.register(WidgetDataCache)
class WidgetDataCacheAdmin(admin.ModelAdmin):
    list_display = ('widget', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('widget__title',)


class EventParticipantInline(admin.TabularInline):
    model = EventParticipant
    extra = 0
    readonly_fields = ('registered_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_time', 'end_time', 'created_by', 'is_public', 'participants_count')
    list_filter = ('event_type', 'is_public', 'start_time', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'
    inlines = [EventParticipantInline]


@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'registered_at', 'attended_at')
    list_filter = ('status', 'registered_at', 'attended_at')
    search_fields = ('event__title', 'user__username', 'feedback')
    readonly_fields = ('registered_at',)
    date_hierarchy = 'registered_at'


class GoalStepInline(admin.TabularInline):
    model = GoalStep
    extra = 0
    readonly_fields = ('created_at', 'completed_at')


@admin.register(StudentGoal)
class StudentGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'goal_type', 'priority', 'due_date', 'is_completed', 'progress')
    list_filter = ('goal_type', 'priority', 'is_completed', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    date_hierarchy = 'created_at'
    inlines = [GoalStepInline]


@admin.register(GoalStep)
class GoalStepAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal', 'order', 'is_completed')
    list_filter = ('is_completed', 'created_at')
    search_fields = ('title', 'description', 'goal__title')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    date_hierarchy = 'created_at'