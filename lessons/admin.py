from django.contrib import admin
from .models import Lesson, LessonContent, LessonCompletion

class LessonContentInline(admin.StackedInline):
    model = LessonContent
    extra = 1

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'course__title')
    inlines = [LessonContentInline]
    ordering = ('course', 'order')

@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'content_type', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('lesson__title', 'content')

@admin.register(LessonCompletion)
class LessonCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed', 'completed_at')
    search_fields = ('user__username', 'lesson__title')
