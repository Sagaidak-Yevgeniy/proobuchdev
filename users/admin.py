from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, UserInterface

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'

class UserInterfaceInline(admin.StackedInline):
    model = UserInterface
    can_delete = False
    verbose_name_plural = 'Настройки интерфейса'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, UserInterfaceInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('profile__role', 'is_staff', 'is_active')
    
    def get_role(self, obj):
        return obj.profile.get_role_display()
    
    get_role.short_description = 'Роль'

class UserInterfaceAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'font_size', 'layout', 'enable_animations', 'high_contrast')
    list_filter = ('theme', 'font_size', 'layout', 'enable_animations', 'high_contrast')
    search_fields = ('user__username', 'user__email')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(UserInterface, UserInterfaceAdmin)
