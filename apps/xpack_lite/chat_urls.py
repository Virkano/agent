from django.urls import path

from xpack_lite.views.chat_auth import (
    LocalChatUserLoginView,
    LocalChatUserLogoutView,
    LocalChatUserProfileView,
    LocalChatUserResetPasswordView,
)

urlpatterns = [
    path('auth/login/<str:access_token>', LocalChatUserLoginView.as_view()),
    path('auth/ldap/login/<str:access_token>', LocalChatUserLoginView.as_view()),
    path('auth/logout', LocalChatUserLogoutView.as_view()),
    path('chat_user/profile', LocalChatUserProfileView.as_view()),
    path('chat_user/current/reset_password', LocalChatUserResetPasswordView.as_view()),
]
