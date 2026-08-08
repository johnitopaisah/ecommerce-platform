from django.urls import path
from . import views

app_name = 'rbac'

urlpatterns = [
    path('roles/', views.role_list, name='role_list'),
    path('roles/<int:group_id>/', views.role_detail, name='role_detail'),
    path('permissions/', views.permission_list, name='permission_list'),

    path('me/permissions/', views.my_permissions, name='my_permissions'),
    path('me/grants/', views.my_grants, name='my_grants'),

    path('requests/', views.request_list_create, name='request_list_create'),
    path('requests/pending/', views.pending_requests, name='pending_requests'),
    path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:request_id>/deny/', views.deny_request, name='deny_request'),
    path('requests/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),

    path('grants/', views.grant_list, name='grant_list'),
    path('grants/<int:grant_id>/revoke/', views.revoke_grant, name='revoke_grant'),
]
