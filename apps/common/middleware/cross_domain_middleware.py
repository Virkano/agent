# coding=utf-8
"""
    @project: dianxin
    @project: dianxin虎
    @file： cross_domain_middleware.py
    @date：2024/5/8 13:36
    @desc:
"""
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from common.cache_data.application_api_key_cache import get_application_api_key
from xpack_lite.models import SystemApiKey


def _get_cross_domain_setting(auth):
    if any([str(auth).startswith(prefix) for prefix in ['Bearer application-', 'Bearer agent-']]):
        return get_application_api_key(str(auth), True)
    if str(auth).startswith('Bearer sk-'):
        api_key = SystemApiKey.objects.filter(secret_key=str(auth)[7:], is_active=True).first()
        if api_key is None:
            return {}
        return {
            'allow_cross_domain': api_key.allow_cross_domain,
            'cross_domain_list': api_key.cross_domain_list,
        }
    return {}


class CrossDomainMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.method == 'OPTIONS':
            return HttpResponse(status=200,
                                headers={
                                    "Access-Control-Allow-Origin": "*",
                                    "Access-Control-Allow-Methods": "GET,POST,DELETE,PUT",
                                    "Access-Control-Allow-Headers": "Origin,X-Requested-With,Content-Type,Accept,Authorization,token"})

    def process_response(self, request, response):
        auth = request.META.get('HTTP_AUTHORIZATION')
        origin = request.META.get('HTTP_ORIGIN')

        if auth is not None and origin is not None:
            key_setting = _get_cross_domain_setting(auth)
            cross_domain_list = key_setting.get('cross_domain_list', [])
            allow_cross_domain = key_setting.get('allow_cross_domain', False)
            if allow_cross_domain:
                response['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,PUT'
                response[
                    'Access-Control-Allow-Headers'] = "Origin,X-Requested-With,Content-Type,Accept,Authorization,token"
                if cross_domain_list is None or len(cross_domain_list) == 0:
                    response['Access-Control-Allow-Origin'] = "*"
                elif cross_domain_list.__contains__(origin):
                    response['Access-Control-Allow-Origin'] = origin
        return response
