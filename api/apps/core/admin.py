from django.contrib import admin
from .models import AdminActionLog


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('created', 'actor', 'action', 'target', 'ip_address')
    list_filter = ('action',)
    search_fields = ('target', 'actor__email')
    readonly_fields = ('actor', 'action', 'target', 'detail', 'ip_address', 'created')
    ordering = ('-created',)

    def has_add_permission(self, request):
        return False  # append-only via log_admin_action(), never through the admin form

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
