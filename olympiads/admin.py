from django.contrib import admin
from django.utils.html import format_html
from .models import Olympiad, Problem, TestCase, Submission, TestResult, OlympiadParticipant


class ProblemInline(admin.TabularInline):
    model = Problem
    extra = 0
    fields = ('title', 'points', 'order')
    show_change_link = True


@admin.register(Olympiad)
class OlympiadAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'status_display', 'problems_count', 'is_published')
    list_filter = ('is_published', 'start_time', 'end_time')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_time'
    inlines = [ProblemInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Расписание', {
            'fields': ('start_time', 'end_time')
        }),
        ('Статус', {
            'fields': ('is_published', 'creator')
        }),
    )
    
    def problems_count(self, obj):
        return obj.problems.count()
    problems_count.short_description = 'Задач'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # если редактируем существующий объект
            return ['creator']
        return []


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0
    fields = ('order', 'is_example', 'input_data', 'expected_output')
    show_change_link = True


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'olympiad', 'points', 'time_limit', 'memory_limit', 'order', 'test_cases_count')
    list_filter = ('olympiad',)
    search_fields = ('title', 'description')
    inlines = [TestCaseInline]
    
    def test_cases_count(self, obj):
        return obj.test_cases.count()
    test_cases_count.short_description = 'Тесты'


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('problem', 'order', 'is_example')
    list_filter = ('problem__olympiad', 'problem', 'is_example')
    search_fields = ('input_data', 'expected_output')


class TestResultInline(admin.TabularInline):
    model = TestResult
    extra = 0
    readonly_fields = ('test_case', 'passed', 'execution_time', 'memory_used', 'output', 'error_message')
    can_delete = False
    max_num = 0
    show_change_link = True


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'status_badge', 'points', 'submitted_at')
    list_filter = ('status', 'problem__olympiad', 'problem')
    search_fields = ('user__username', 'problem__title', 'code')
    readonly_fields = ('submitted_at',)
    date_hierarchy = 'submitted_at'
    inlines = [TestResultInline]
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#777',
            'testing': '#007bff',
            'accepted': '#28a745',
            'wrong_answer': '#dc3545',
            'time_limit': '#fd7e14',
            'memory_limit': '#fd7e14',
            'runtime_error': '#dc3545',
            'compilation_error': '#dc3545',
            'system_error': '#6f42c1',
        }
        color = status_colors.get(obj.status, '#777')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Статус'


@admin.register(OlympiadParticipant)
class OlympiadParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'olympiad', 'total_points', 'solved_problems', 'registered_at')
    list_filter = ('olympiad',)
    search_fields = ('user__username', 'olympiad__title')
    readonly_fields = ('registered_at', 'total_points', 'solved_problems')
    date_hierarchy = 'registered_at'
    actions = ['update_statistics']
    
    def update_statistics(self, request, queryset):
        for participant in queryset:
            participant.update_statistics()
        self.message_user(request, f"Статистика обновлена для {queryset.count()} участников.")
    update_statistics.short_description = "Обновить статистику выбранных участников"