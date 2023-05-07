from django.contrib import admin
from django.contrib.auth.admin import admin

# Register your models here.
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_at',
                    'is_admin', 'is_active', 'is_superuser', 'is_staff',
                    'is_verified', 'auth_provider')
    search_fields = ('email',)
    readonly_fields = ('created_at', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(User, UserAdmin)
