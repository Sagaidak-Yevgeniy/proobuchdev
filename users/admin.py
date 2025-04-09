from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('profile__role', 'is_staff', 'is_active')
    
    def get_role(self, obj):
        return obj.profile.get_role_display()
    
    get_role.short_description = 'Роль'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile)
