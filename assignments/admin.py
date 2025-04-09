from django.contrib import admin
from .models import Assignment, AssignmentSubmission, TestCase

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson_content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'task_description', 'lesson_content__lesson__title')
    inlines = [TestCaseInline]

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'assignment', 'score', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at')
    search_fields = ('user__username', 'assignment__title', 'code')

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'input_data', 'expected_output')
    search_fields = ('assignment__title', 'input_data', 'expected_output')
