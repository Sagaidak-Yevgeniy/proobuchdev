from django.contrib import admin
from .models import ChatSession, ChatMessage, CodeSnippet, AIFeedback


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'course', 'lesson', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'course__title', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


class CodeSnippetInline(admin.TabularInline):
    model = CodeSnippet
    extra = 0


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('get_session_title', 'role', 'get_content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'session__title')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [CodeSnippetInline]
    
    def get_session_title(self, obj):
        return obj.session.title
    get_session_title.short_description = 'Сессия'
    
    def get_content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    get_content_preview.short_description = 'Содержание'


@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    list_display = ('get_message_id', 'language', 'line_start', 'created_at')
    list_filter = ('language', 'created_at')
    search_fields = ('code', 'message__content')
    readonly_fields = ('created_at',)
    
    def get_message_id(self, obj):
        return f"Сообщение #{obj.message.id}"
    get_message_id.short_description = 'Сообщение'


@admin.register(AIFeedback)
class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'get_message_id', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment', 'user__username')
    readonly_fields = ('created_at',)
    
    def get_message_id(self, obj):
        return f"Сообщение #{obj.message.id}"
    get_message_id.short_description = 'Сообщение'