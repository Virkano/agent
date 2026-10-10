# coding=utf-8
import json
from datetime import datetime, time, timedelta

import openpyxl
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.views import APIView

from common.auth.authenticate import TokenAuth
from common.exception.app_exception import AppApiException
from common.log.log import log
from common.log.labels import expand_menu_labels, normalize_menu_label, normalize_operate_label
from common.result import result
from system_manage.models import Log, SettingType, SystemSetting
from xpack_lite.models import Workspace
from xpack_lite.services import is_admin, page_result


DEFAULT_CLEAN_TIME = 180

def _require_admin(request):
    if not request.user or not is_admin(request.user.id):
        raise AppApiException(403, 'No permission to access')


def _loads_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        loaded = json.loads(value)
        return loaded if isinstance(loaded, list) else []
    except Exception:
        return []


def _parse_datetime_bound(value, is_end=False):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            return None
        parsed = datetime.combine(parsed_date, time.max if is_end else time.min)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _get_clean_time():
    setting = SystemSetting.objects.filter(type=SettingType.LOG.value).first()
    if not setting:
        return DEFAULT_CLEAN_TIME
    try:
        return int((setting.meta or {}).get('clean_time', DEFAULT_CLEAN_TIME))
    except Exception:
        return DEFAULT_CLEAN_TIME


def _serialize_log(log_item, workspace_name_map=None):
    workspace_name_map = workspace_name_map or {}
    workspace_id = log_item.workspace_id
    return {
        'id': str(log_item.id),
        'menu': log_item.menu,
        'menu_label': normalize_menu_label(log_item.menu),
        'operate': normalize_operate_label(log_item.operate),
        'operation_object': log_item.operation_object or {},
        'user': log_item.user or {},
        'status': log_item.status,
        'ip_address': log_item.ip_address,
        'details': log_item.details or {},
        'workspace_id': workspace_id,
        'workspace_name': workspace_name_map.get(workspace_id, '默认空间' if workspace_id in ['default', 'None', None] else ''),
        'create_time': log_item.create_time,
        'update_time': log_item.update_time,
    }


def _filter_queryset(params):
    queryset = Log.objects.all().order_by('-create_time')
    start_time = _parse_datetime_bound(params.get('start_time'))
    end_time = _parse_datetime_bound(params.get('end_time'), is_end=True)
    if start_time:
        queryset = queryset.filter(create_time__gte=start_time)
    if end_time:
        queryset = queryset.filter(create_time__lte=end_time)

    username = params.get('user')
    if username:
        queryset = queryset.filter(
            Q(user__username__icontains=username)
            | Q(user__nick_name__icontains=username)
            | Q(user__email__icontains=username)
            | Q(user__id__icontains=username)
        )

    ip_address = params.get('ip_address')
    if ip_address:
        queryset = queryset.filter(ip_address__icontains=ip_address)

    status = params.get('status')
    if status:
        queryset = queryset.filter(status=int(status))

    menus = _loads_list(params.get('menu'))
    if menus:
        queryset = queryset.filter(menu__in=expand_menu_labels(menus))

    workspace_ids = _loads_list(params.get('workspace_ids'))
    if workspace_ids:
        queryset = queryset.filter(workspace_id__in=workspace_ids)
    return queryset


def _workspace_name_map(queryset):
    workspace_ids = set(queryset.exclude(workspace_id__in=['default', 'None']).values_list('workspace_id', flat=True))
    return {str(item.id): item.name for item in Workspace.objects.filter(id__in=workspace_ids)}


class OperateLogMenuOptionView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request):
        _require_admin(request)
        menus = list(
            Log.objects.exclude(menu='')
            .values_list('menu', flat=True)
            .distinct()
            .order_by('menu')
        )
        labels = sorted({normalize_menu_label(menu) for menu in menus})
        return result.success([{'menu': label, 'menu_label': label} for label in labels])


class OperateLogView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request, current_page, page_size):
        _require_admin(request)
        queryset = _filter_queryset(request.query_params)
        workspace_names = _workspace_name_map(queryset)
        return result.success(page_result(
            queryset,
            current_page,
            page_size,
            lambda item: _serialize_log(item, workspace_names),
        ))


class OperateLogExportView(APIView):
    authentication_classes = [TokenAuth]

    @log(menu='日志管理', operate='导出全局操作日志')
    def post(self, request):
        _require_admin(request)
        queryset = _filter_queryset(request.query_params)
        workspace_names = _workspace_name_map(queryset)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = '操作日志'
        worksheet.append(['菜单', '操作详情', '用户', '工作空间', '状态', 'IP 地址', '操作时间', '详情'])
        for item in queryset:
            row = _serialize_log(item, workspace_names)
            worksheet.append([
                row['menu_label'],
                row['operate'],
                (row['user'] or {}).get('username') or (row['user'] or {}).get('id', ''),
                row['workspace_name'],
                '成功' if row['status'] == 200 else '失败',
                row['ip_address'],
                timezone.localtime(row['create_time']).strftime('%Y-%m-%d %H:%M:%S') if row['create_time'] else '',
                json.dumps(row['details'], ensure_ascii=False),
            ])
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="log.xlsx"'
        workbook.save(response)
        workbook.close()
        return response


class OperateLogCleanTimeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request):
        _require_admin(request)
        return result.success(_get_clean_time())

    @log(menu='日志管理', operate='更新日志清理策略')
    def post(self, request):
        _require_admin(request)
        clean_time = int(request.data.get('clean_time') or DEFAULT_CLEAN_TIME)
        if clean_time < 1:
            raise AppApiException(500, 'clean_time must be greater than 0')
        setting, _ = SystemSetting.objects.get_or_create(type=SettingType.LOG.value)
        setting.meta = {'clean_time': clean_time}
        setting.save()
        Log.objects.filter(create_time__lt=timezone.now() - timedelta(days=clean_time)).delete()
        return result.success(clean_time)
