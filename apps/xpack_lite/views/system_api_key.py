# coding=utf-8
import hashlib

import uuid_utils.compat as uuid
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView

from common.auth import TokenAuth
from common.exception.app_exception import AppApiException
from common.log.log import log
from common.result import result
from xpack_lite.models import SystemApiKey
from xpack_lite.services import page_result


def _generate_secret_key():
    return 'sk-' + hashlib.md5(str(uuid.uuid7()).encode()).hexdigest()


def _serialize_api_key(api_key):
    return {
        'id': str(api_key.id),
        'user_id': str(api_key.user_id),
        'secret_key': api_key.secret_key,
        'is_active': api_key.is_active,
        'allow_cross_domain': api_key.allow_cross_domain,
        'cross_domain_list': api_key.cross_domain_list or [],
        'expire_time': api_key.expire_time,
        'is_permanent': api_key.is_permanent,
        'create_time': api_key.create_time,
        'update_time': api_key.update_time,
    }


def _get_user_api_key(request, api_key_id):
    api_key = QuerySet(SystemApiKey).filter(id=api_key_id, user_id=request.user.id).first()
    if api_key is None:
        raise AppApiException(500, 'APIKey does not exist')
    return api_key


def _set_expire_time(api_key, data):
    if 'is_permanent' not in data:
        return
    api_key.is_permanent = bool(data.get('is_permanent'))
    if api_key.is_permanent:
        api_key.expire_time = timezone.now()
        return
    expire_time = data.get('expire_time')
    if not expire_time:
        raise AppApiException(500, 'Expiration time cannot be empty')
    parsed_expire_time = parse_datetime(expire_time) if isinstance(expire_time, str) else expire_time
    if parsed_expire_time is None:
        raise AppApiException(500, 'Expiration time is invalid')
    if timezone.is_naive(parsed_expire_time):
        parsed_expire_time = timezone.make_aware(parsed_expire_time, timezone.get_current_timezone())
    api_key.expire_time = parsed_expire_time


class SystemApiKeyView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request, current_page, page_size):
        order_by = request.query_params.get('order_by') or '-create_time'
        if order_by.lstrip('-') not in {'create_time', 'update_time', 'expire_time', 'secret_key'}:
            order_by = '-create_time'
        queryset = QuerySet(SystemApiKey).filter(user_id=request.user.id).order_by(order_by)
        return result.success(page_result(queryset, current_page, page_size, _serialize_api_key))

    @log(menu='System API Key', operate='Add API Key')
    def post(self, request):
        api_key = SystemApiKey(
            id=uuid.uuid7(),
            user_id=request.user.id,
            secret_key=_generate_secret_key(),
        )
        api_key.save()
        return result.success(_serialize_api_key(api_key))


class SystemApiKeyOperateView(APIView):
    authentication_classes = [TokenAuth]

    @log(menu='System API Key', operate='Modify API Key')
    def put(self, request, api_key_id):
        api_key = _get_user_api_key(request, api_key_id)
        data = request.data or {}
        if 'is_active' in data:
            api_key.is_active = bool(data.get('is_active'))
        if 'allow_cross_domain' in data:
            api_key.allow_cross_domain = bool(data.get('allow_cross_domain'))
        if 'cross_domain_list' in data and data.get('cross_domain_list') is not None:
            api_key.cross_domain_list = [item for item in data.get('cross_domain_list') if item]
        _set_expire_time(api_key, data)
        api_key.save()
        return result.success(_serialize_api_key(api_key))

    @log(menu='System API Key', operate='Delete API Key')
    def delete(self, request, api_key_id):
        api_key = _get_user_api_key(request, api_key_id)
        api_key.delete()
        return result.success(True)
