import json
from functools import wraps

from rest_framework.request import Request
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from common.auth.authenticate import TokenAuth
from common.exception.app_exception import AppApiException
from common.result import result
from xpack_lite.models import SharedResourceWorkspaceAuthorization, Workspace, WorkspaceUserRoleMapping
from xpack_lite.services import get_authorized_knowledge, get_authorized_tool, is_admin, page_result


def _require_admin(request):
    if not is_admin(request.user.id):
        raise AppApiException(403, 'No permission to access')


def _require_workspace_member(request, workspace_id):
    if is_admin(request.user.id):
        return
    if not WorkspaceUserRoleMapping.objects.filter(workspace_id=workspace_id, user_id=request.user.id).exists():
        raise AppApiException(403, 'No permission to access')


def _normalize_shared_resource_type(resource_type):
    resource_type = (resource_type or '').upper()
    if resource_type not in {'KNOWLEDGE', 'TOOL', 'MODEL'}:
        raise AppApiException(400, 'Unsupported shared resource type')
    return resource_type


def _ensure_shared_resource_exists(resource_type, resource_id):
    resource_type = _normalize_shared_resource_type(resource_type)
    if resource_type == 'KNOWLEDGE':
        from knowledge.models import Knowledge, KnowledgeScope

        exists = Knowledge.objects.filter(id=resource_id, scope=KnowledgeScope.SHARED).exists()
    elif resource_type == 'TOOL':
        from tools.models import Tool, ToolScope

        exists = Tool.objects.filter(id=resource_id, scope=ToolScope.SHARED).exists()
    else:
        from models_provider.models import Model

        exists = Model.objects.filter(id=resource_id, workspace_id='None').exists()
    if not exists:
        raise AppApiException(404, 'Shared resource does not exist')
    return resource_type


def _get_shared_knowledge(knowledge_id):
    from knowledge.models import Knowledge, KnowledgeScope

    knowledge = Knowledge.objects.filter(id=knowledge_id, scope=KnowledgeScope.SHARED).first()
    if knowledge is None:
        raise AppApiException(404, 'Shared knowledge does not exist')
    return knowledge


def shared_knowledge_route(view_class):
    view = view_class.as_view()

    @wraps(view)
    def route(request, *args, **kwargs):
        knowledge = _get_shared_knowledge(kwargs.get('knowledge_id'))
        kwargs['workspace_id'] = knowledge.workspace_id
        return view(request, *args, **kwargs)

    return route


def shared_default_workspace_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = 'default'
        return view(request, *args, **kwargs)

    return route


def shared_none_workspace_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = 'None'
        return view(request, *args, **kwargs)

    return route


def shared_resource_workspace_route(view_class):
    view = view_class.as_view()

    @wraps(view)
    def route(request, *args, **kwargs):
        kwargs['workspace_id'] = 'default'
        return view(request, *args, **kwargs)

    return route


def _get_resource_workspace_id(model_class, resource_id, id_field='id'):
    resource = model_class.objects.filter(**{id_field: resource_id}).first()
    if resource is None:
        raise AppApiException(404, 'Resource does not exist')
    return resource.workspace_id


def system_application_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        from application.models import Application

        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = _get_resource_workspace_id(Application, kwargs.get('application_id'))
        return view(request, *args, **kwargs)

    return route


def system_knowledge_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        from knowledge.models import Knowledge

        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = _get_resource_workspace_id(Knowledge, kwargs.get('knowledge_id'))
        return view(request, *args, **kwargs)

    return route


def system_tool_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        from tools.models import Tool

        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = _get_resource_workspace_id(Tool, kwargs.get('tool_id'))
        return view(request, *args, **kwargs)

    return route


def system_model_route(view_class, drop_kwargs=None):
    view = view_class.as_view()
    drop_kwargs = drop_kwargs or []

    @wraps(view)
    def route(request, *args, **kwargs):
        from models_provider.models import Model

        for key in drop_kwargs:
            kwargs.pop(key, None)
        kwargs['workspace_id'] = _get_resource_workspace_id(Model, kwargs.get('model_id'))
        return view(request, *args, **kwargs)

    return route


def _workspace_names():
    return {workspace.id: workspace.name for workspace in Workspace.objects.all()}


def _json_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def _filter_common(queryset, params):
    name = params.get('name')
    create_user = params.get('create_user')
    workspace_ids = _json_list(params.get('workspace_ids'))
    if name:
        queryset = queryset.filter(name__icontains=name)
    if create_user:
        queryset = queryset.filter(user_id=create_user)
    if workspace_ids:
        queryset = queryset.filter(workspace_id__in=workspace_ids)
    return queryset


def _user_name(row):
    user = getattr(row, 'user', None)
    if not user:
        return ''
    return user.nick_name or user.username


def _base_resource(row, workspace_names):
    return {
        'id': str(row.id),
        'name': row.name,
        'workspace_id': row.workspace_id,
        'workspace_name': workspace_names.get(row.workspace_id, row.workspace_id),
        'create_user': str(row.user_id) if row.user_id else '',
        'create_user_name': _user_name(row),
        'nick_name': _user_name(row),
        'user_id': str(row.user_id) if row.user_id else '',
        'user_name': _user_name(row),
        'create_time': row.create_time,
        'update_time': row.update_time,
        'resource_count': 0,
    }


class SystemResourceApplicationView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from application.models import Application

        params = request.query_params
        queryset = Application.objects.select_related('user').order_by('-create_time')
        queryset = _filter_common(queryset, params)
        app_type = params.get('type')
        status = _json_list(params.get('status'))
        if app_type:
            queryset = queryset.filter(type=app_type)
        if status:
            queryset = queryset.filter(is_publish__in=[str(item).lower() == 'true' for item in status])
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'icon': row.icon,
                'type': row.type,
                'is_publish': row.is_publish,
                'publish_time': row.publish_time,
                'dialogue_number': row.dialogue_number,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemResourceApplicationExportView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, application_id: str):
        _require_admin(request)
        from application.serializers.application import ApplicationOperateSerializer
        from application.models import Application

        workspace_id = _get_resource_workspace_id(Application, application_id)
        return ApplicationOperateSerializer(data={
            'application_id': application_id,
            'workspace_id': workspace_id,
            'user_id': request.user.id,
        }).export()


class SystemResourceAuthorizationView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str, target: str, resource: str):
        _require_admin(request)
        from system_manage.serializers.user_resource_permission import ResourceUserPermissionSerializer

        return result.success(ResourceUserPermissionSerializer(data={
            'workspace_id': workspace_id,
            'target': target,
            'auth_target_type': resource.replace('_FOLDER', ''),
        }).list({
            'username': request.query_params.get('username'),
            'role': request.query_params.get('role'),
            'nick_name': request.query_params.get('nick_name'),
            'permission': request.query_params.getlist('permission[]'),
        }))

    def put(self, request: Request, workspace_id: str, target: str, resource: str):
        _require_admin(request)
        from system_manage.serializers.user_resource_permission import ResourceUserPermissionSerializer

        return result.success(ResourceUserPermissionSerializer(data={
            'workspace_id': workspace_id,
            'target': target,
            'auth_target_type': resource.replace('_FOLDER', ''),
        }).edit(instance=request.data, current_user_id=request.user.id))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, target: str, resource: str, current_page: int,
                page_size: int):
            _require_admin(request)
            from system_manage.serializers.user_resource_permission import ResourceUserPermissionSerializer

            return result.success(ResourceUserPermissionSerializer(data={
                'workspace_id': workspace_id,
                'target': target,
                'auth_target_type': resource.replace('_FOLDER', ''),
            }).page({
                'username': request.query_params.get('username'),
                'role': request.query_params.get('role'),
                'nick_name': request.query_params.get('nick_name'),
                'permission': request.query_params.getlist('permission[]'),
            }, current_page, page_size))


class SystemResourceKnowledgeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from django.db.models import Count, Sum
        from django.db.models.functions import Coalesce
        from knowledge.models import Knowledge

        params = request.query_params
        queryset = (
            Knowledge.objects.select_related('user')
            .annotate(document_count=Count('document'), char_length=Coalesce(Sum('document__char_length'), 0))
            .order_by('-create_time')
        )
        queryset = _filter_common(queryset, params)
        knowledge_type = params.get('type')
        if knowledge_type not in (None, ''):
            queryset = queryset.filter(type=knowledge_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'type': row.type,
                'scope': row.scope,
                'embedding_model_id': str(row.embedding_model_id) if row.embedding_model_id else '',
                'meta': row.meta,
                'document_count': row.document_count,
                'char_length': row.char_length,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemResourceToolView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from tools.models import Tool

        params = request.query_params
        queryset = Tool.objects.select_related('user').order_by('-create_time')
        queryset = _filter_common(queryset, params)
        tool_type = params.get('tool_type')
        source = params.get('source')
        if tool_type:
            queryset = queryset.filter(tool_type=tool_type)
        if source == 'STORE':
            queryset = queryset.exclude(template_id__isnull=True).exclude(template_id='')
        elif source == 'CUSTOM':
            queryset = queryset.filter(template_id__isnull=True)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'icon': row.icon,
                'is_active': row.is_active,
                'scope': row.scope,
                'tool_type': row.tool_type,
                'template_id': row.template_id,
                'init_field_list': row.init_field_list,
                'input_field_list': row.input_field_list,
                'init_params': row.init_params,
                'label': row.label,
                'version': row.version,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemResourceToolOperateView(APIView):
    authentication_classes = [TokenAuth]

    def _workspace_id(self, tool_id):
        from tools.models import Tool

        return _get_resource_workspace_id(Tool, tool_id)

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(
            data={'id': tool_id, 'workspace_id': self._workspace_id(tool_id)}
        ).one())

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(
            data={'id': tool_id, 'workspace_id': self._workspace_id(tool_id)}
        ).edit(request.data))

    def delete(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(
            data={'id': tool_id, 'workspace_id': self._workspace_id(tool_id)}
        ).delete())


class SystemResourceToolWorkflowView(APIView):
    authentication_classes = [TokenAuth]

    def _serializer(self, request, tool_id):
        from tools.models import Tool
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return ToolWorkflowSerializer.Operate(data={
            'user_id': request.user.id,
            'workspace_id': _get_resource_workspace_id(Tool, tool_id),
            'tool_id': tool_id,
        })

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        return result.success(self._serializer(request, tool_id).one())

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        return result.success(self._serializer(request, tool_id).edit(request.data))


class SystemResourceToolPublishView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.models import Tool
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return result.success(ToolWorkflowSerializer.Operate(data={
            'user_id': request.user.id,
            'workspace_id': _get_resource_workspace_id(Tool, tool_id),
            'tool_id': tool_id,
        }).publish())


class SystemResourceToolVersionView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.models import Tool
        from tools.serializers.tool_version import ToolWorkflowVersionSerializer

        return result.success(ToolWorkflowVersionSerializer.Query(
            data={'workspace_id': _get_resource_workspace_id(Tool, tool_id)}
        ).list({'name': request.query_params.get('name'), 'tool_id': tool_id}))

    class Page(APIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, tool_id: str, current_page: int, page_size: int):
            _require_admin(request)
            from tools.models import Tool
            from tools.serializers.tool_version import ToolWorkflowVersionSerializer

            return result.success(ToolWorkflowVersionSerializer.Query(
                data={'workspace_id': _get_resource_workspace_id(Tool, tool_id)}
            ).page({'name': request.query_params.get('name'), 'tool_id': tool_id}, current_page, page_size))

    class Operate(APIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, tool_id: str, tool_version_id: str):
            _require_admin(request)
            from tools.models import Tool
            from tools.serializers.tool_version import ToolWorkflowVersionSerializer

            return result.success(ToolWorkflowVersionSerializer.Operate(data={
                'workspace_id': _get_resource_workspace_id(Tool, tool_id),
                'tool_id': tool_id,
                'tool_version_id': tool_version_id,
            }).one())

        def put(self, request: Request, tool_id: str, tool_version_id: str):
            _require_admin(request)
            from tools.models import Tool
            from tools.serializers.tool_version import ToolWorkflowVersionSerializer

            return result.success(ToolWorkflowVersionSerializer.Operate(data={
                'workspace_id': _get_resource_workspace_id(Tool, tool_id),
                'tool_id': tool_id,
                'tool_version_id': tool_version_id,
            }).edit(request.data))


class SystemResourceModelView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from models_provider.models import Model

        params = request.query_params
        queryset = Model.objects.select_related('user').order_by('-create_time')
        queryset = _filter_common(queryset, params)
        model_type = params.get('model_type')
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'status': row.status,
                'model_type': row.model_type,
                'model_name': row.model_name,
                'provider': row.provider,
                'meta': row.meta,
                'model_params_form': row.model_params_form,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemSharedKnowledgeView(SystemResourceKnowledgeView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from knowledge.models import KnowledgeScope
        from knowledge.serializers.knowledge import KnowledgeSerializer

        payload = request.data.copy()
        payload['folder_id'] = payload.get('folder_id') or 'default'
        workspace_id = payload.get('workspace_id') or 'default'
        return result.success(KnowledgeSerializer.Create(
            data={
                'user_id': request.user.id,
                'workspace_id': workspace_id,
                'scope': KnowledgeScope.SHARED,
            }
        ).save_base(payload))

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from django.db.models import Count, Sum
        from django.db.models.functions import Coalesce
        from knowledge.models import Knowledge

        params = request.query_params
        queryset = (
            Knowledge.objects.select_related('user')
            .filter(scope='SHARED')
            .annotate(document_count=Count('document'), char_length=Coalesce(Sum('document__char_length'), 0))
            .order_by('-create_time')
        )
        queryset = _filter_common(queryset, params)
        knowledge_type = params.get('type')
        if knowledge_type not in (None, ''):
            queryset = queryset.filter(type=knowledge_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'type': row.type,
                'scope': row.scope,
                'embedding_model_id': str(row.embedding_model_id) if row.embedding_model_id else '',
                'meta': row.meta,
                'document_count': row.document_count,
                'char_length': row.char_length,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class WorkspaceSharedKnowledgeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str, current_page=None, page_size=None):
        _require_workspace_member(request, workspace_id)
        from django.db.models import Count, Sum
        from django.db.models.functions import Coalesce
        from knowledge.models import Knowledge

        params = request.query_params
        queryset = (
            Knowledge.objects.select_related('user')
            .filter(scope='SHARED')
            .annotate(document_count=Count('document'), char_length=Coalesce(Sum('document__char_length'), 0))
            .order_by('-create_time')
        )
        queryset = get_authorized_knowledge(queryset, workspace_id)
        queryset = _filter_common(queryset, params)
        knowledge_type = params.get('type')
        if knowledge_type not in (None, ''):
            queryset = queryset.filter(type=knowledge_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'type': row.type,
                'scope': row.scope,
                'embedding_model_id': str(row.embedding_model_id) if row.embedding_model_id else '',
                'meta': row.meta,
                'document_count': row.document_count,
                'char_length': row.char_length,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemSharedWorkspaceAuthorizationView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, resource_type: str, resource_id: str):
        _require_admin(request)
        resource_type = _ensure_shared_resource_exists(resource_type, resource_id)
        auth = SharedResourceWorkspaceAuthorization.objects.filter(
            id=resource_id,
            resource_type=resource_type,
        ).first()
        return result.success({
            'authentication_type': auth.authentication_type if auth else 'WHITE_LIST',
            'workspace_id_list': auth.workspace_id_list if auth else [],
        })

    def post(self, request: Request, resource_type: str, resource_id: str):
        _require_admin(request)
        resource_type = _ensure_shared_resource_exists(resource_type, resource_id)
        authentication_type = request.data.get('authentication_type') or 'WHITE_LIST'
        if authentication_type not in {'WHITE_LIST', 'BLACK_LIST'}:
            raise AppApiException(400, 'Unsupported authentication type')
        workspace_id_list = [str(workspace_id) for workspace_id in (request.data.get('workspace_id_list') or [])]
        invalid_workspace_ids = [
            workspace_id
            for workspace_id in workspace_id_list
            if not Workspace.objects.filter(id=workspace_id).exists()
        ]
        if invalid_workspace_ids:
            raise AppApiException(400, f'Workspace does not exist: {",".join(invalid_workspace_ids)}')
        SharedResourceWorkspaceAuthorization.objects.update_or_create(
            id=resource_id,
            defaults={
                'resource_type': resource_type,
                'authentication_type': authentication_type,
                'workspace_id_list': workspace_id_list,
            },
        )
        return result.success(True)


class SystemSharedKnowledgeWebView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from knowledge.models import KnowledgeScope
        from knowledge.serializers.knowledge import KnowledgeSerializer

        payload = request.data.copy()
        payload['folder_id'] = payload.get('folder_id') or 'default'
        workspace_id = payload.get('workspace_id') or 'default'
        return result.success(KnowledgeSerializer.Create(
            data={
                'user_id': request.user.id,
                'workspace_id': workspace_id,
                'scope': KnowledgeScope.SHARED,
            }
        ).save_web(payload))


class SystemSharedKnowledgeWorkflowView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from knowledge.models import KnowledgeScope
        from knowledge.serializers.knowledge_workflow import KnowledgeWorkflowSerializer

        payload = request.data.copy()
        payload['folder_id'] = payload.get('folder_id') or 'default'
        workspace_id = payload.get('workspace_id') or 'default'
        return result.success(KnowledgeWorkflowSerializer.Create(
            data={
                'user_id': request.user.id,
                'workspace_id': workspace_id,
                'scope': KnowledgeScope.SHARED,
            }
        ).save_workflow(payload))


class SystemSharedKnowledgeImportView(APIView):
    authentication_classes = [TokenAuth]
    parser_classes = [MultiPartParser]

    def post(self, request: Request):
        _require_admin(request)
        from knowledge.models import KnowledgeScope
        from knowledge.serializers.knowledge import KnowledgeSerializer

        workspace_id = request.data.get('workspace_id') or 'default'
        return result.success(KnowledgeSerializer.ImportKnowledge(
            data={
                'workspace_id': workspace_id,
                'user_id': request.user.id,
                'folder_id': request.data.get('folder_id') or 'default',
                'scope': KnowledgeScope.SHARED,
            }
        ).import_knowledge(request.FILES.get('file'), True))


class SystemSharedKnowledgeModelListView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, model_type: str = 'LLM', knowledge_id: str = None):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(ModelSerializer.Query(
            data={
                'user_id': str(request.user.id),
                'workspace_id': 'None',
                'model_type': model_type,
            }
        ).share_list('None', True))


class SystemSharedKnowledgeOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.knowledge import KnowledgeSerializer

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(KnowledgeSerializer.Operate(
            data={
                'user_id': request.user.id,
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
            }
        ).one())

    def put(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.knowledge import KnowledgeSerializer

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(KnowledgeSerializer.Operate(
            data={
                'user_id': request.user.id,
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
            }
        ).edit(request.data))

    def delete(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.knowledge import KnowledgeSerializer

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(KnowledgeSerializer.Operate(
            data={
                'user_id': request.user.id,
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
            }
        ).delete())


class SystemSharedDocumentView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        raw_tags = request.query_params.getlist('tags[]')
        return result.success(DocumentSerializers.Query(
            data={
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
                'folder_id': request.query_params.get('folder_id'),
                'name': request.query_params.get('name'),
                'tag': request.query_params.get('tag'),
                'tag_exclude': request.query_params.get('tag_exclude'),
                'tag_ids': [tag for tag in raw_tags if tag != 'NO_TAG'],
                'no_tag': 'NO_TAG' in raw_tags,
                'desc': request.query_params.get('desc'),
                'user_id': request.query_params.get('user_id'),
            }
        ).list())

    def post(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(DocumentSerializers.Create(
            data={
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
                'user_id': request.user.id,
            }
        ).save(request.data))


class SystemSharedDocumentPageView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, knowledge_id: str, current_page: int, page_size: int):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        raw_tags = request.query_params.getlist('tags[]')
        return result.success(DocumentSerializers.Query(
            data={
                'workspace_id': knowledge.workspace_id,
                'knowledge_id': knowledge_id,
                'folder_id': request.query_params.get('folder_id'),
                'name': request.query_params.get('name'),
                'tag': request.query_params.get('tag'),
                'tag_exclude': request.query_params.get('tag_exclude'),
                'tag_ids': [tag for tag in raw_tags if tag != 'NO_TAG'],
                'no_tag': 'NO_TAG' in raw_tags,
                'desc': request.query_params.get('desc'),
                'user_id': request.query_params.get('user_id'),
                'status': request.query_params.get('status'),
                'is_active': request.query_params.get('is_active'),
                'hit_handling_method': request.query_params.get('hit_handling_method'),
                'order_by': request.query_params.get('order_by'),
                'create_user': request.query_params.get('create_user'),
            }
        ).page(current_page, page_size))


class SystemSharedDocumentBatchCreateView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, knowledge_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(DocumentSerializers.Batch(
            data={
                'knowledge_id': knowledge_id,
                'workspace_id': knowledge.workspace_id,
                'user_id': request.user.id,
            }
        ).batch_save(request.data))


class SystemSharedDocumentOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, knowledge_id: str, document_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        operate = DocumentSerializers.Operate(
            data={'document_id': document_id, 'knowledge_id': knowledge_id, 'workspace_id': knowledge.workspace_id}
        )
        operate.is_valid(raise_exception=True)
        return result.success(operate.one())

    def put(self, request: Request, knowledge_id: str, document_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        return result.success(DocumentSerializers.Operate(
            data={'document_id': document_id, 'knowledge_id': knowledge_id, 'workspace_id': knowledge.workspace_id}
        ).edit(request.data, with_valid=True))

    def delete(self, request: Request, knowledge_id: str, document_id: str):
        _require_admin(request)
        from knowledge.serializers.document import DocumentSerializers

        knowledge = _get_shared_knowledge(knowledge_id)
        operate = DocumentSerializers.Operate(
            data={'document_id': document_id, 'knowledge_id': knowledge_id, 'workspace_id': knowledge.workspace_id}
        )
        operate.is_valid(raise_exception=True)
        return result.success(operate.delete())


class SystemSharedToolView(SystemResourceToolView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from tools.models import ToolScope
        from tools.serializers.tool import ToolSerializer

        payload = request.data.copy()
        payload['folder_id'] = payload.get('folder_id') or 'default'
        payload['scope'] = ToolScope.SHARED
        return result.success(
            ToolSerializer.Create(data={'user_id': request.user.id, 'workspace_id': 'None'}).insert(payload)
        )

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from tools.models import Tool

        params = request.query_params
        queryset = Tool.objects.select_related('user').filter(scope='SHARED').order_by('-create_time')
        queryset = _filter_common(queryset, params)
        tool_type = params.get('tool_type')
        if tool_type:
            queryset = queryset.filter(tool_type=tool_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'icon': row.icon,
                'is_active': row.is_active,
                'scope': row.scope,
                'tool_type': row.tool_type,
                'template_id': row.template_id,
                'init_field_list': row.init_field_list,
                'input_field_list': row.input_field_list,
                'init_params': row.init_params,
                'label': row.label,
                'version': row.version,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class WorkspaceSharedToolView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str, current_page=None, page_size=None):
        _require_workspace_member(request, workspace_id)
        from tools.models import Tool

        params = request.query_params
        queryset = Tool.objects.select_related('user').filter(scope='SHARED').order_by('-create_time')
        queryset = get_authorized_tool(queryset, workspace_id)
        queryset = _filter_common(queryset, params)
        tool_type = params.get('tool_type')
        if tool_type:
            queryset = queryset.filter(tool_type=tool_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'desc': row.desc,
                'icon': row.icon,
                'is_active': row.is_active,
                'scope': row.scope,
                'tool_type': row.tool_type,
                'template_id': row.template_id,
                'init_field_list': row.init_field_list,
                'input_field_list': row.input_field_list,
                'init_params': row.init_params,
                'label': row.label,
                'version': row.version,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemSharedToolOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(data={'id': tool_id, 'workspace_id': 'None'}).one())

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(data={'id': tool_id, 'workspace_id': 'None'}).edit(request.data))

    def delete(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Operate(data={'id': tool_id, 'workspace_id': 'None'}).delete())


class SystemSharedToolDebugView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.Debug(data={'workspace_id': 'None', 'user_id': request.user.id}).debug(request.data)
        )


class SystemSharedToolTestConnectionView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.TestConnection(data={'workspace_id': 'None', 'code': request.data.get('code')}).test_connection()
        )


class SystemSharedToolPylintView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(ToolSerializer.Pylint(data={'workspace_id': 'None'}).run(request.data))


class SystemSharedToolImportView(APIView):
    authentication_classes = [TokenAuth]
    parser_classes = [MultiPartParser]

    def post(self, request: Request):
        _require_admin(request)
        from tools.models import ToolScope
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.Import(
                data={
                    'workspace_id': 'None',
                    'file': request.FILES.get('file'),
                    'user_id': request.user.id,
                    'folder_id': request.data.get('folder_id') or 'default',
                }
            ).import_(ToolScope.SHARED)
        )


class SystemSharedToolAddInternalView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, tool_id: str):
        _require_admin(request)
        import uuid_utils.compat as uuid
        from django.db.models import QuerySet
        from tools.models import Tool, ToolScope, ToolType
        from tools.serializers.tool import AddInternalToolRequest, ToolModelSerializer

        AddInternalToolRequest(data=request.data).is_valid(raise_exception=True)
        internal_tool = QuerySet(Tool).filter(id=tool_id, scope=ToolScope.INTERNAL).first()
        if internal_tool is None:
            raise AppApiException(500, 'Tool does not exist')

        shared_tool = Tool(
            id=uuid.uuid7(),
            name=request.data.get('name') or internal_tool.name,
            desc=internal_tool.desc,
            code=internal_tool.code,
            user_id=request.user.id,
            icon=internal_tool.icon,
            workspace_id='None',
            input_field_list=internal_tool.input_field_list,
            init_field_list=internal_tool.init_field_list,
            scope=ToolScope.SHARED,
            tool_type=ToolType.CUSTOM,
            folder_id=request.data.get('folder_id') or 'default',
            template_id=internal_tool.id,
            label=internal_tool.label,
            is_active=False,
        )
        shared_tool.save()
        return result.success(ToolModelSerializer(shared_tool).data)


class SystemSharedToolAddStoreView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, tool_id: str):
        _require_admin(request)
        import base64
        import io
        import requests
        import uuid_utils.compat as uuid
        from common.utils.url_validator import ALLOWED_CALLBACK_HOSTS, ALLOWED_DOWNLOAD_HOSTS, validate_trusted_url
        from knowledge.models import File, FileSourceType
        from tools.models import Tool, ToolScope, ToolType
        from tools.serializers.tool import AddInternalToolRequest, RestrictedUnpickler, ToolModelSerializer

        AddInternalToolRequest(data=request.data).is_valid(raise_exception=True)
        versions = request.data.get('versions', [])
        download_url = request.data.get('download_url')
        if not validate_trusted_url(download_url, ALLOWED_DOWNLOAD_HOSTS):
            raise AppApiException(500, 'Illegal download url')
        version_name = next((version.get('name') for version in versions if version.get('downloadUrl') == download_url))
        response = requests.get(download_url, timeout=5, allow_redirects=False)
        tool_data = RestrictedUnpickler(io.BytesIO(response.content)).load().tool
        shared_tool_id = uuid.uuid7()

        code = tool_data.get('code')
        if tool_data.get('tool_type') == ToolType.SKILL:
            skill_file_id = uuid.uuid7()
            skill_file = File(
                id=skill_file_id,
                file_name=f"{tool_data.get('name')}.zip",
                source_type=FileSourceType.TOOL,
                source_id=shared_tool_id,
                meta={},
            )
            skill_file.save(base64.b64decode(code))
            code = skill_file_id

        shared_tool = Tool(
            id=shared_tool_id,
            name=request.data.get('name'),
            desc=tool_data.get('desc'),
            code=code,
            user_id=request.user.id,
            icon=request.data.get('icon', ''),
            workspace_id='None',
            input_field_list=tool_data.get('input_field_list', []),
            init_field_list=tool_data.get('init_field_list', []),
            scope=ToolScope.SHARED,
            tool_type=tool_data.get('tool_type', ToolType.CUSTOM),
            folder_id=request.data.get('folder_id') or 'default',
            template_id=tool_id,
            label=request.data.get('label'),
            version=version_name,
            is_active=False,
        )
        shared_tool.save()

        try:
            callback_url = request.data.get('download_callback_url')
            if validate_trusted_url(callback_url, ALLOWED_CALLBACK_HOSTS):
                requests.get(callback_url, timeout=5, allow_redirects=False)
        except Exception:
            pass

        return result.success(ToolModelSerializer(shared_tool).data)


class SystemSharedToolUpdateStoreView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, tool_id: str):
        _require_admin(request)
        import base64
        import io
        import requests
        import uuid_utils.compat as uuid
        from django.db.models import QuerySet
        from common.utils.url_validator import ALLOWED_CALLBACK_HOSTS, ALLOWED_DOWNLOAD_HOSTS, validate_trusted_url
        from knowledge.models import File, FileSourceType
        from tools.models import Tool, ToolScope, ToolType
        from tools.serializers.tool import RestrictedUnpickler, ToolModelSerializer

        shared_tool = QuerySet(Tool).filter(id=tool_id, scope=ToolScope.SHARED).first()
        if shared_tool is None:
            raise AppApiException(500, 'Tool does not exist')
        download_url = request.data.get('download_url')
        if not validate_trusted_url(download_url, ALLOWED_DOWNLOAD_HOSTS):
            raise AppApiException(500, 'Illegal download url')
        version_name = next(
            (version.get('name') for version in request.data.get('versions', []) if version.get('downloadUrl') == download_url)
        )
        response = requests.get(download_url, timeout=5, allow_redirects=False)
        tool_data = RestrictedUnpickler(io.BytesIO(response.content)).load().tool
        code = tool_data.get('code')

        if tool_data.get('tool_type') == ToolType.SKILL:
            if shared_tool.tool_type == ToolType.SKILL and shared_tool.code:
                QuerySet(File).filter(id=shared_tool.code).delete()
            skill_file_id = uuid.uuid7()
            skill_file = File(
                id=skill_file_id,
                file_name=f"{tool_data.get('name')}.zip",
                source_type=FileSourceType.TOOL,
                source_id=shared_tool.id,
                meta={},
            )
            skill_file.save(base64.b64decode(code))
            code = skill_file_id

        shared_tool.desc = tool_data.get('desc')
        shared_tool.code = code
        shared_tool.input_field_list = tool_data.get('input_field_list', [])
        shared_tool.init_field_list = tool_data.get('init_field_list', [])
        shared_tool.icon = request.data.get('icon', shared_tool.icon)
        shared_tool.version = version_name
        shared_tool.tool_type = tool_data.get('tool_type', ToolType.CUSTOM)
        shared_tool.label = request.data.get('label')
        shared_tool.save()

        try:
            callback_url = request.data.get('download_callback_url')
            if validate_trusted_url(callback_url, ALLOWED_CALLBACK_HOSTS):
                requests.get(callback_url, timeout=5, allow_redirects=False)
        except Exception:
            pass

        return result.success(ToolModelSerializer(shared_tool).data)


class SystemSharedToolIconView(APIView):
    authentication_classes = [TokenAuth]
    parser_classes = [MultiPartParser]

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.IconOperate(
                data={
                    'id': tool_id,
                    'workspace_id': 'None',
                    'user_id': request.user.id,
                    'image': request.FILES.get('file'),
                }
            ).edit(request.data)
        )


class SystemSharedToolExportView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return ToolSerializer.Operate(data={'id': tool_id, 'workspace_id': 'None'}).export()


class SystemSharedToolSkillFileView(APIView):
    authentication_classes = [TokenAuth]
    parser_classes = [MultiPartParser]

    def put(self, request: Request):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.UploadSkillFile(
                data={'workspace_id': 'None', 'user_id': request.user.id, 'file': request.FILES.get('file')}
            ).upload()
        )


class SystemSharedToolDownloadSkillFileView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return ToolSerializer.DownloadSkillFile(
            data={'workspace_id': 'None', 'user_id': request.user.id, 'tool_id': tool_id}
        ).download()


class SystemSharedToolGenerateCodeView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return ToolSerializer.GenerateCodeSerializer(data={'workspace_id': 'None', **request.data}).generate_code()


class SystemSharedToolWorkflowView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return result.success(
            ToolWorkflowSerializer.Operate(
                data={'user_id': request.user.id, 'workspace_id': 'None', 'tool_id': tool_id}
            ).one()
        )

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return result.success(
            ToolWorkflowSerializer.Operate(
                data={'user_id': request.user.id, 'workspace_id': 'None', 'tool_id': tool_id}
            ).edit(request.data)
        )


class SystemSharedToolWorkflowPublishView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return result.success(
            ToolWorkflowSerializer.Operate(
                data={'tool_id': tool_id, 'user_id': request.user.id, 'workspace_id': 'None'}
            ).publish()
        )


class SystemSharedToolWorkflowDebugView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool_workflow import ToolWorkflowSerializer

        return ToolWorkflowSerializer.Operate(
            data={'workspace_id': 'None', 'tool_id': tool_id, 'user_id': request.user.id}
        ).debug(request.data, request.user, True)


class SystemSharedToolWorkflowImportView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request, tool_id: str):
        _require_admin(request)
        raise AppApiException(501, 'Tool workflow import is not supported')


class SystemSharedToolRecordPageView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str, current_page: int, page_size: int):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.ToolRecord(
                data={
                    'tool_id': tool_id,
                    'workspace_id': 'None',
                    'source_name': request.query_params.get('source_name'),
                    'source_type': request.query_params.get('source_type'),
                    'state': request.query_params.get('state'),
                }
            ).get_tool_records(current_page, page_size)
        )


class SystemSharedToolRecordOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str, record_id: str):
        _require_admin(request)
        from tools.serializers.tool import ToolSerializer

        return result.success(
            ToolSerializer.ToolRecord.Operate(
                data={'tool_id': tool_id, 'workspace_id': 'None', 'id': record_id}
            ).one()
        )


class SystemSharedToolWorkflowVersionView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str):
        _require_admin(request)
        from tools.serializers.tool_version import ToolWorkflowVersionSerializer

        return result.success(
            ToolWorkflowVersionSerializer.Query(data={'workspace_id': 'None'}).list(
                {'name': request.query_params.get('name'), 'tool_id': tool_id}
            )
        )


class SystemSharedToolWorkflowVersionPageView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str, current_page: int, page_size: int):
        _require_admin(request)
        from tools.serializers.tool_version import ToolWorkflowVersionSerializer

        return result.success(
            ToolWorkflowVersionSerializer.Query(data={'workspace_id': 'None'}).page(
                {'name': request.query_params.get('name'), 'tool_id': tool_id},
                current_page,
                page_size,
            )
        )


class SystemSharedToolWorkflowVersionOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, tool_id: str, tool_version_id: str):
        _require_admin(request)
        from tools.serializers.tool_version import ToolWorkflowVersionSerializer

        return result.success(
            ToolWorkflowVersionSerializer.Operate(
                data={
                    'user_id': request.user.id,
                    'workspace_id': 'None',
                    'tool_id': tool_id,
                    'tool_version_id': tool_version_id,
                }
            ).one()
        )

    def put(self, request: Request, tool_id: str, tool_version_id: str):
        _require_admin(request)
        from tools.serializers.tool_version import ToolWorkflowVersionSerializer

        return result.success(
            ToolWorkflowVersionSerializer.Operate(
                data={
                    'user_id': request.user.id,
                    'workspace_id': 'None',
                    'tool_id': tool_id,
                    'tool_version_id': tool_version_id,
                }
            ).edit(request.data)
        )


class SystemSharedModelView(SystemResourceModelView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Create(
                data={**request.data, 'user_id': request.user.id, 'workspace_id': 'None'}
            ).insert('None', with_valid=True)
        )

    def get(self, request: Request, current_page=None, page_size=None):
        _require_admin(request)
        from models_provider.models import Model

        params = request.query_params
        queryset = Model.objects.select_related('user').filter(workspace_id='None').order_by('-create_time')
        queryset = _filter_common(queryset, params)
        model_type = params.get('model_type')
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        workspace_names = _workspace_names()

        def serialize(row):
            data = _base_resource(row, workspace_names)
            data.update({
                'status': row.status,
                'model_type': row.model_type,
                'model_name': row.model_name,
                'provider': row.provider,
                'meta': row.meta,
                'model_params_form': row.model_params_form,
            })
            return data

        if current_page and page_size:
            return result.success(page_result(queryset, current_page, page_size, serialize))
        return result.success([serialize(row) for row in queryset[:200]])


class SystemSharedModelOperateView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Operate(data={'id': model_id, 'user_id': request.user.id, 'workspace_id': 'None'}).one(
                with_valid=True
            )
        )

    def put(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Operate(data={'id': model_id, 'user_id': request.user.id, 'workspace_id': 'None'}).edit(
                request.data, str(request.user.id), with_valid=False
            )
        )

    def delete(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Operate(data={'id': model_id, 'user_id': request.user.id, 'workspace_id': 'None'}).delete(
                with_valid=False
            )
        )


class SystemSharedModelMetaView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Operate(data={'id': model_id, 'workspace_id': 'None'}).one_meta(with_valid=True)
        )


class SystemSharedModelParamsFormView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.ModelParams(data={'id': model_id, 'workspace_id': 'None'}).get_model_params()
        )

    def put(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.ModelParams(data={'id': model_id, 'workspace_id': 'None'}).save_model_params_form(
                request.data
            )
        )


class SystemSharedModelPauseDownloadView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, model_id: str):
        _require_admin(request)
        from models_provider.serializers.model_serializer import ModelSerializer

        return result.success(
            ModelSerializer.Operate(data={'id': model_id, 'workspace_id': 'None'}).pause_download(with_valid=False)
        )
