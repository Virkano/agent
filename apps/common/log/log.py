# coding=utf-8
"""
    @project: dianxin
    @project: dianxin虎
    @file： log.py
    @date：2025/6/4 14:13
    @desc:
"""
from system_manage.models.log_management import Log

from common.log.labels import normalize_menu_label, normalize_operate_label


def _get_ip_address(request):
    """
    获取ip地址
    @param request:
    @return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _get_user(request):
    """
    获取用户
    @param request:
    @return:
    """
    user = request.user
    if user is None:
        return {

        }
    user_info = {
        "id": str(user.id),
        "email": user.email,
        "phone": user.phone,
        "nick_name": user.nick_name,
        "username": user.username,
    }
    # 如果是 User 模型且有 role 属性
    if hasattr(user, 'role'):
        user_info['role'] = user.role
    return user_info


def _get_details(request):
    """Store request structure, never arbitrary values or URL path parameters."""
    match = getattr(request, 'resolver_match', None)
    body = getattr(request, 'data', None)
    query = getattr(request, 'query_params', None)
    return {
        'route_template': getattr(match, 'route', None) or 'UNRESOLVED',
        'body_fields': sorted(str(key) for key in body.keys()) if hasattr(body, 'keys') else [],
        'query_fields': sorted(str(key) for key in query.keys()) if hasattr(query, 'keys') else [],
    }


def _safe_actor(user):
    if not isinstance(user, dict):
        return {}
    return {key: str(user[key]) for key in ('id', 'role') if user.get(key) is not None}


def _safe_operation_object(value):
    if not isinstance(value, dict):
        return {}
    return {'field_names': sorted(str(key) for key in value.keys())}


def _get_workspace_id(request, kwargs):
    return kwargs.get('workspace_id', 'None')


def log(menu: str, operate, get_user=_get_user, get_ip_address=_get_ip_address, get_details=_get_details,
        get_operation_object=None, get_workspace_id=_get_workspace_id):
    """
    记录审计日志
    @param menu: 操作菜单 str
    @param operate: 操作 str|func 如果是一个函数 入参将是一个request 响应为str def operate(request): return "操作菜单"
    @param get_user: 获取用户
    @param get_ip_address:获取IP地址
    @param get_details: 获取执行详情
    @param get_operation_object: 获取操作对象
    @param get_workspace_id: 获取工作空间id
    @return:
    """

    def inner(func):
        def run(view, request, **kwargs):
            status = 200
            operation_object = {}
            try:
                if get_operation_object is not None:
                    operation_object = get_operation_object(request, kwargs)
            except Exception:
                pass
            try:
                return func(view, request, **kwargs)
            except Exception as e:
                status = getattr(e, 'status_code', 500)
                raise e
            finally:
                ip = get_ip_address(request)
                user = _safe_actor(get_user(request))
                details = _get_details(request)
                workspace_id = get_workspace_id(request, kwargs)
                _operate = operate
                if callable(operate):
                    _operate = operate(request)
                # 插入审计日志
                Log(menu=normalize_menu_label(menu), operate=normalize_operate_label(_operate),
                    user=user, status=status, ip_address=ip, details=details,
                    operation_object=_safe_operation_object(operation_object), workspace_id=workspace_id).save()

        return run

    return inner


def record_log(menu: str, operate: str, request, user: dict = None, status: int = 200,
               get_details=_get_details, get_operation_object=None, workspace_id: str = 'default',
               operation_object: dict = None):
    """
    手动记录审计日志（适用于无法使用装饰器的场景，如第三方登录回调）

    @param menu: 操作菜单，如 'Chat User/login'
    @param operate: 操作描述，如 'Log in'
    @param request: Django Request 对象
    @param user: 用户信息字典，包含 id, username, email 等字段
    @param status: 状态码，默认 200
    @param get_details: 获取请求详情的函数
    @param get_operation_object: 获取操作对象的函数，如果提供则优先使用
    @param get_workspace_id: 获取工作空间 ID 的函数
    @param operation_object: 操作对象字典，如 {'name': 'username'}
    @param workspace_id: 工作空间 ID，默认 'default'
    @return: None
    """
    try:
        ip = _get_ip_address(request)
        details = _get_details(request)

        # 如果提供了 get_operation_object 函数，优先使用它获取操作对象
        if operation_object is None and get_operation_object is not None:
            try:
                operation_object = get_operation_object(request, {})
            except Exception:
                operation_object = {}
        Log(
            menu=normalize_menu_label(menu),
            operate=normalize_operate_label(operate),
            user=_safe_actor(user),
            status=status,
            ip_address=ip,
            details=details,
            operation_object=_safe_operation_object(operation_object),
            workspace_id=workspace_id
        ).save()
    except Exception:
        # 日志记录失败不应影响主业务流程
        pass
