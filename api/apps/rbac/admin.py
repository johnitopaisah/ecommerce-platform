from django.contrib import admin
from .models import RoleGrant, RoleGrantRequest


@admin.register(RoleGrant)
class RoleGrantAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'status', 'granted_by', 'granted_at', 'expires_at')
    list_filter = ('status', 'group')
    search_fields = ('user__email', 'group__name')
    readonly_fields = ('granted_by', 'granted_at', 'revoked_by', 'revoked_at')


@admin.register(RoleGrantRequest)
class RoleGrantRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'group', 'status', 'duration_hours', 'reviewed_by', 'created')
    list_filter = ('status', 'group')
    search_fields = ('requester__email', 'group__name')
    readonly_fields = ('requester', 'group', 'duration_hours', 'justification', 'created')
