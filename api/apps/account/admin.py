from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserBase


@admin.register(UserBase)
class UserBaseAdmin(UserAdmin):
    list_display = ('email', 'user_name', 'first_name', 'last_name', 'is_active', 'is_staff', 'created')
    list_filter = ('is_active', 'is_staff', 'country')
    search_fields = ('email', 'user_name', 'first_name', 'last_name')
    ordering = ('-created',)

    fieldsets = (
        (None, {'fields': ('email', 'user_name', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'about', 'phone_number')}),
        ('Address', {'fields': ('country', 'address_line_1', 'address_line_2', 'town_city', 'postcode')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created', 'updated')}),
    )
    readonly_fields = ('created', 'updated', 'last_login')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_name', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
