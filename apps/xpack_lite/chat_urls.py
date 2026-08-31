from django.urls import path

from xpack_lite.views.chat_auth import (
    DingTalkChatUserCallbackView,
    LocalChatUserLoginView,
    LocalChatUserLogoutView,
    LocalChatUserProfileView,
    LocalChatUserResetPasswordView,
    PublicChatQrPlatformSourceView,
    PublicChatQrTypeView,
)

urlpatterns = [
    path('auth/login/<str:access_token>', LocalChatUserLoginView.as_view()),
    path('auth/ldap/login/<str:access_token>', LocalChatUserLoginView.as_view()),
    path('auth/dingtalk', DingTalkChatUserCallbackView.as_view()),
    path('auth/dingtalk/oauth2', DingTalkChatUserCallbackView.as_view()),
    path('auth/qr_type', PublicChatQrTypeView.as_view()),
    path('auth/qr_type/source', PublicChatQrPlatformSourceView.as_view()),
    path('auth/logout', LocalChatUserLogoutView.as_view()),
    path('chat_user/profile', LocalChatUserProfileView.as_view()),
    path('chat_user/current/reset_password', LocalChatUserResetPasswordView.as_view()),
]
