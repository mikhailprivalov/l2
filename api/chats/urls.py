from django.urls import path

from . import views

urlpatterns = [
    path('mark-as-online-user', views.mark_as_online_user),
    path('mark-as-offline-user', views.mark_as_offline_user),
    path('get-users-for-hospital', views.get_users_for_hospital),
    path('get-messages-count', views.get_messages_count),
    path('get-dialog-id', views.get_dialog_pk),
    path('get-dialog-data', views.get_dialog_data),
    path('send-message', views.send_message),
    path('get-notify-token', views.get_notify_token),
    path('get-messages', views.get_messages),
    path('get-messages-feature', views.get_messages_feature),
    path('read-messages', views.read_messages),
    path('get-read-statuses', views.get_read_statuses),
]
