from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Olympiad, 
    OlympiadTask, 
    OlympiadTestCase, 
    OlympiadMultipleChoiceOption,
    OlympiadParticipation, 
    OlympiadTaskSubmission,
    OlympiadInvitation,
    OlympiadCertificate
)

class OlympiadTestCaseInline(admin.TabularInline):
    model = OlympiadTestCase
    extra = 1
    fields = ('input_data', 'expected_output', 'is_hidden', 'points', 'order')
    
class OlympiadMultipleChoiceOptionInline(admin.TabularInline):
    model = OlympiadMultipleChoiceOption
    extra = 2
    fields = ('text', 'is_correct', 'explanation', 'order')

class OlympiadTaskInline(admin.TabularInline):
    model = OlympiadTask
    extra = 0
    fields = ('title', 'task_type', 'points', 'order', 'min_passing_score')
    show_change_link = True

@admin.register(OlympiadTask)
class OlympiadTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'olympiad', 'task_type', 'points', 'order')
    list_filter = ('olympiad', 'task_type')
    search_fields = ('title', 'description', 'olympiad__title')
    ordering = ('olympiad', 'order')
    fieldsets = (
        (None, {
            'fields': ('olympiad', 'title', 'description', 'task_type', 'order')
        }),
        (_('Настройки'), {
            'fields': ('points', 'min_passing_score', 'time_limit_minutes', 'memory_limit_mb')
        }),
        (_('Программирование'), {
            'fields': ('initial_code',),
            'classes': ('collapse',),
            'description': _('Настройки для заданий типа "Программирование"')
        }),
    )
    inlines = [OlympiadTestCaseInline, OlympiadMultipleChoiceOptionInline]

@admin.register(Olympiad)
class OlympiadAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'status', 'is_open', 'created_by')
    list_filter = ('status', 'is_open', 'is_rated', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    date_hierarchy = 'start_datetime'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'short_description', 'description', 'image', 'status')
        }),
        (_('Время проведения'), {
            'fields': ('start_datetime', 'end_datetime', 'time_limit_minutes')
        }),
        (_('Настройки доступа'), {
            'fields': ('is_open', 'is_rated', 'min_passing_score', 'related_course')
        }),
        (_('Дополнительная информация'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OlympiadTaskInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если это новая олимпиада
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(OlympiadParticipation)
class OlympiadParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'olympiad', 'started_at', 'score', 'is_completed', 'passed')
    list_filter = ('is_completed', 'passed', 'started_at')
    search_fields = ('user__username', 'olympiad__title')
    readonly_fields = ('started_at', 'finished_at', 'score', 'max_score')

@admin.register(OlympiadTaskSubmission)
class OlympiadTaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('participation', 'task', 'score', 'is_correct', 'submitted_at')
    list_filter = ('is_correct', 'submitted_at')
    search_fields = ('participation__user__username', 'task__title')
    readonly_fields = ('submitted_at', 'execution_time', 'memory_usage')

@admin.register(OlympiadInvitation)
class OlympiadInvitationAdmin(admin.ModelAdmin):
    list_display = ('olympiad', 'code', 'description', 'is_active', 'used_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('olympiad__title', 'code', 'description')

@admin.register(OlympiadCertificate)
class OlympiadCertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'participation', 'issue_date')
    search_fields = ('certificate_id', 'participation__user__username', 'participation__olympiad__title')
    readonly_fields = ('issue_date',)