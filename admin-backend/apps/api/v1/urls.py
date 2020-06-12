from django.urls import path, include
from apps.api.v1.common import apis as common_apis
from apps.api.v1.users import apis as users_apis

users_urlpatterns = [
    path(r'delete/<str:attendeecode>/', users_apis.delete_user),
    path(r'createbulk/<int:amount>/', users_apis.create_users),
    path(r'taskstatus/<str:task_id>/', users_apis.query_process_update)
]
common_urlpatterns = [
    path(r'getsettings/', common_apis.get_settings),
]

app_name = 'v1'
urlpatterns = [
    path('users/', include((users_urlpatterns, 'users'))),
    path('common/', include((common_urlpatterns, 'common'))),
]