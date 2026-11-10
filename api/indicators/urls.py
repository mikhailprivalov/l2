from django.urls import path

from . import views

urlpatterns = [
    path('search-indicator', views.search_indicator),
    path('save-indicator-value', views.save_indicator_value),
    path('approval-journal', views.approval_journal),
    path('approval-journal/link', views.approval_journal_link),
    path('approval-journal/link-open', views.approval_journal_link_open),
    path('approval-journal/sign', views.approval_journal_sign),
    path('approval-journal/sign-reset', views.approval_journal_sign_reset),
]
