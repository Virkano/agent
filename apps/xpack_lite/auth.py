from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from application.models import ApplicationAccessToken, ChatUserType
from common.auth.common import ChatUserToken
from common.auth.handle.auth_base_handle import AuthBaseHandle
from common.auth.handle.impl.user_token import get_auth
from common.constants.authentication_type import AuthenticationType
from common.constants.permission_constants import ChatAuth, Group, Operate, Permission, RoleConstants
from common.exception.app_exception import AppAuthenticationFailed
from system_manage.models.chat_user import ChatUser
from xpack_lite.models import SystemApiKey
from xpack_lite.services import is_auth_chat_user


class ChatUserTokenAuth(AuthBaseHandle):
    def support(self, request, token: str, get_token_details):
        token_details = get_token_details()
        if token_details is None:
            return False
        return (
            'application_id' in token_details
            and 'access_token' in token_details
            and token_details.get('type') == AuthenticationType.CHAT_USER.value
        )

    def handle(self, request, token: str, get_token_details):
        chat_user_token = ChatUserToken.new_instance(get_token_details())
        application_access_token = QuerySet(ApplicationAccessToken).filter(
            application_id=chat_user_token.application_id,
            access_token=chat_user_token.access_token,
            is_active=True,
        ).first()
        if application_access_token is None:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        chat_user = QuerySet(ChatUser).filter(id=chat_user_token.chat_user_id, is_active=True).first()
        if chat_user is None:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        if (
            application_access_token.authentication
            and application_access_token.authentication_value.get('type') == 'login'
            and not is_auth_chat_user(chat_user.id, application_access_token.application_id)
        ):
            raise AppAuthenticationFailed(1002, _('The chat user is not authorized.'))
        return None, ChatAuth(
            current_role_list=[RoleConstants.CHAT_USER],
            permission_list=[Permission(group=Group.APPLICATION, operate=Operate.USE)],
            application_id=application_access_token.application_id,
            chat_user_id=str(chat_user.id),
            chat_user_type=ChatUserType.CHAT_USER.value,
        )


class SystemApiKeyAuth(AuthBaseHandle):
    def support(self, request, token: str, get_token_details):
        return token.startswith('sk-')

    def handle(self, request, token: str, get_token_details):
        api_key = QuerySet(SystemApiKey).filter(secret_key=token).select_related('user').first()
        if api_key is None:
            raise AppAuthenticationFailed(1002, _('Secret key is invalid'))
        if not api_key.is_active:
            raise AppAuthenticationFailed(1002, _('Secret key is invalid'))
        if not api_key.is_permanent and api_key.expire_time < timezone.now():
            raise AppAuthenticationFailed(1002, _('Secret key is expired'))
        if not api_key.user.is_active:
            raise AppAuthenticationFailed(1002, _('Authentication information is incorrect'))
        return api_key.user, get_auth(api_key.user)
