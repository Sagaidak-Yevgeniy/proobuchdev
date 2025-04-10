from django.contrib import admin
from .models import Course, Enrollment, Category, CourseCompletion
from .models_certificates import Certificate, CertificateTemplate

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'is_published')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at', 'is_completed')
    list_filter = ('enrolled_at', 'is_completed')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'enrolled_at'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'completion_date', 'percentage', 'certificate_generated')
    list_filter = ('completion_date', 'certificate_generated')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'completion_date'

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'user', 'certificate_type', 'title', 'issued_date', 'status')
    list_filter = ('certificate_type', 'status', 'issued_date')
    search_fields = ('title', 'user__username', 'certificate_id')
    date_hierarchy = 'issued_date'
    readonly_fields = ('certificate_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('certificate_id', 'user', 'certificate_type', 'title', 'description', 'status')
        }),
        ('Связи', {
            'fields': ('course', 'olympiad', 'achievement', 'template_used')
        }),
        ('Даты', {
            'fields': ('issued_date', 'expiry_date', 'created_at', 'updated_at')
        }),
        ('Результаты', {
            'fields': ('earned_points', 'max_points', 'completion_percentage')
        }),
        ('Файлы', {
            'fields': ('pdf_file', 'qr_code')
        }),
    )

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Дизайн', {
            'fields': ('background_image', 'logo_image', 'title_color', 'text_color')
        }),
        ('Шрифты', {
            'fields': ('title_font_size', 'text_font_size', 'recipient_name_font_size')
        }),
        ('Тексты', {
            'fields': ('title_text', 'subtitle_text', 'footer_text')
        }),
    )
