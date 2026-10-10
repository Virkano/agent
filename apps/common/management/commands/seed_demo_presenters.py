"""Create role-based presenter accounts for local demonstrations.

Passwords are generated with ``secrets`` and written only to an owner-readable,
git-ignored local file.  The command never writes a plaintext password to stdout.
"""

import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.constants.cache_version import Cache_Version
from common.constants.permission_constants import (
    PermissionConstants,
    ResourceAuthType,
    ResourcePermission,
    RoleConstants,
)
from system_manage.models import AuthTargetType, WorkspaceUserResourcePermission
from telecom_ai_agent.conf import PROJECT_DIR
from users.models import User
from xpack_lite.models import (
    RolePermissionMapping,
    RoleSetting,
    Workspace,
    WorkspaceUserRoleMapping,
)


@dataclass(frozen=True)
class PresenterDefinition:
    username: str
    nick_name: str
    title: str
    base_role: str
    bind_base_role: bool
    additional_roles: tuple[str, ...]
    custom_role_id: str | None
    custom_role_type: str | None
    permission_names: tuple[str, ...]
    workspace_scope: str
    resource_access: str | None


AI_PERMISSION_PREFIXES = ("APPLICATION_", "KNOWLEDGE_", "MODEL_", "TOOL_")


def _permission_names_with_prefixes(*prefixes):
    return tuple(
        item.name
        for item in PermissionConstants
        if item.name == "HOMEPAGE_READ" or item.name.startswith(prefixes)
    )


PRESENTERS = (
    PresenterDefinition(
        username="demo_platform_admin",
        nick_name="演示-平台管理员",
        title="平台管理员",
        base_role=RoleConstants.ADMIN.name,
        bind_base_role=True,
        additional_roles=(RoleConstants.WORKSPACE_MANAGE.name, RoleConstants.USER.name),
        custom_role_id=None,
        custom_role_type=None,
        permission_names=(),
        workspace_scope="all",
        resource_access=None,
    ),
    PresenterDefinition(
        username="demo_ai_engineer",
        nick_name="演示-AI知识工程师",
        title="AI 与知识工程师",
        base_role=RoleConstants.USER.name,
        bind_base_role=False,
        additional_roles=(),
        custom_role_id="DEMO_AI_KNOWLEDGE_ENGINEER",
        custom_role_type=RoleConstants.USER.name,
        permission_names=_permission_names_with_prefixes(*AI_PERMISSION_PREFIXES)
        + ("PLATFORM_MONITORING_READ",),
        workspace_scope="all",
        resource_access=ResourcePermission.MANAGE,
    ),
    PresenterDefinition(
        username="demo_marketing_operator",
        nick_name="演示-营销运营专员",
        title="营销运营专员",
        base_role=RoleConstants.USER.name,
        bind_base_role=True,
        additional_roles=(),
        custom_role_id="DEMO_MARKETING_OPERATOR",
        custom_role_type=RoleConstants.USER.name,
        permission_names=(
            "HOMEPAGE_READ",
            "APPLICATION_READ",
            "APPLICATION_OVERVIEW_READ",
            "APPLICATION_CHAT_LOG_READ",
            "KNOWLEDGE_READ",
            "MARKETING_SCENARIO_READ",
            "MARKETING_CAMPAIGN_READ",
            "MARKETING_TASK_READ",
            "RECOMMENDATION_ENGINE_READ",
            "MARKETING_OPERATIONS_READ",
            "ANALYSIS_REPORT_READ",
        ),
        workspace_scope="business",
        resource_access=ResourcePermission.VIEW,
    ),
    PresenterDefinition(
        username="demo_quality_duty",
        nick_name="演示-质检值班专员",
        title="质检与值班专员",
        base_role=RoleConstants.USER.name,
        bind_base_role=False,
        additional_roles=(),
        custom_role_id="DEMO_QUALITY_DUTY",
        custom_role_type=RoleConstants.USER.name,
        permission_names=(
            "HOMEPAGE_READ",
            "HOMEPAGE_EXPORT",
            "MODEL_READ",
            "MODEL_EDIT",
            "APPLICATION_READ",
            "APPLICATION_CHAT_LOG_READ",
            "APPLICATION_CHAT_LOG_ANNOTATION",
            "APPLICATION_CHAT_LOG_EXPORT",
            "KNOWLEDGE_READ",
            "MARKETING_OPERATIONS_READ",
            "MARKETING_QUALITY_READ",
            "ANALYSIS_REPORT_READ",
            "METRIC_OPERATIONS_READ",
            "PLATFORM_MONITORING_READ",
        ),
        workspace_scope="all",
        resource_access=ResourcePermission.VIEW,
    ),
    PresenterDefinition(
        username="demo_rehearsal_lead",
        nick_name="演示-调度演练负责人",
        title="调度与演练负责人",
        base_role=RoleConstants.WORKSPACE_MANAGE.name,
        bind_base_role=True,
        additional_roles=(),
        custom_role_id="DEMO_ORCHESTRATION_REHEARSAL_LEAD",
        custom_role_type=RoleConstants.WORKSPACE_MANAGE.name,
        permission_names=_permission_names_with_prefixes("TRIGGER_", "TOOL_")
        + (
            "APPLICATION_READ",
            "MODEL_READ",
            "API_ORCHESTRATION_READ",
            "EVENT_ORCHESTRATION_READ",
            "RESOURCE_COORDINATION_READ",
            "IVR_SIMULATOR_READ",
            "REHEARSAL_READ",
        ),
        workspace_scope="all",
        resource_access=ResourcePermission.VIEW,
    ),
)


class Command(BaseCommand):
    help = "Create or refresh role-based demo presenter accounts without printing passwords"

    def add_arguments(self, parser):
        parser.add_argument(
            "--primary-workspace-id",
            default="default",
            help="Workspace used for platform and AI capability demonstrations",
        )
        parser.add_argument(
            "--business-workspace-id",
            help="Workspace used for marketing, monitoring and rehearsal demonstrations",
        )
        parser.add_argument(
            "--credentials-file",
            type=Path,
            default=Path(PROJECT_DIR) / ".local_runtime" / "demo-presenter-accounts.txt",
            help="Owner-readable local plaintext credentials file (must stay outside Git)",
        )
        parser.add_argument(
            "--rotate-passwords",
            action="store_true",
            help="Rotate all presenter passwords and replace the local credentials file",
        )

    def handle(self, *args, **options):
        primary = self._get_workspace(options["primary_workspace_id"], "primary")
        business_id = options["business_workspace_id"] or primary.id
        business = self._get_workspace(business_id, "business")
        workspaces = list({workspace.id: workspace for workspace in (primary, business)}.values())
        self._require_builtin_roles()

        credentials = []
        summaries = []
        with transaction.atomic():
            custom_roles = self._upsert_custom_roles()
            for definition in PRESENTERS:
                target_workspaces = self._resolve_workspaces(
                    definition.workspace_scope,
                    primary,
                    business,
                    workspaces,
                )
                user, created = User.objects.get_or_create(
                    username=definition.username,
                    defaults={
                        "nick_name": definition.nick_name,
                        "role": definition.base_role,
                        "source": "LOCAL",
                        "is_active": True,
                    },
                )
                user.nick_name = definition.nick_name
                user.role = definition.base_role
                user.source = "LOCAL"
                user.is_active = True

                if created or options["rotate_passwords"]:
                    plaintext = self._new_password()
                    user.set_password(plaintext)
                    credentials.append((definition, plaintext, target_workspaces))
                user.save()

                self._replace_role_bindings(
                    user,
                    definition,
                    target_workspaces,
                    custom_roles,
                )
                self._replace_resource_permissions(
                    user,
                    target_workspaces,
                    definition.resource_access,
                )
                transaction.on_commit(
                    lambda current_user=user: self._clear_auth_cache(current_user)
                )
                summaries.append((definition, created, target_workspaces))

        credentials_path = options["credentials_file"].expanduser().resolve()
        if credentials:
            self._write_credentials(credentials_path, credentials)
        elif options["rotate_passwords"]:
            raise CommandError("Password rotation was requested but no credentials were generated")

        for definition, created, target_workspaces in summaries:
            state = "created" if created else "updated"
            workspace_names = ", ".join(workspace.name for workspace in target_workspaces)
            self.stdout.write(f"{definition.username}: {state}; {definition.title}; {workspace_names}")
        if credentials:
            self.stdout.write(
                self.style.SUCCESS(
                    f"PASS: {len(summaries)} presenter accounts ready; credentials saved to "
                    f"{credentials_path} with mode 0600"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "PASS: presenter accounts refreshed without password rotation; existing credentials were not changed"
                )
            )

    @staticmethod
    def _get_workspace(workspace_id, label):
        try:
            return Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist as exc:
            raise CommandError(f"Unknown {label} workspace: {workspace_id}") from exc

    @staticmethod
    def _require_builtin_roles():
        required = {
            RoleConstants.ADMIN.name,
            RoleConstants.WORKSPACE_MANAGE.name,
            RoleConstants.USER.name,
        }
        existing = set(RoleSetting.objects.filter(id__in=required).values_list("id", flat=True))
        missing = sorted(required - existing)
        if missing:
            raise CommandError(f"Missing built-in roles: {', '.join(missing)}")

    @staticmethod
    def _upsert_custom_roles():
        result = {}
        known_permissions = {item.name: str(item.value) for item in PermissionConstants}
        for definition in PRESENTERS:
            if not definition.custom_role_id:
                continue
            role, _ = RoleSetting.objects.update_or_create(
                id=definition.custom_role_id,
                defaults={
                    "role_name": f"演示-{definition.title}",
                    "type": definition.custom_role_type,
                    "internal": False,
                },
            )
            missing = sorted(set(definition.permission_names) - set(known_permissions))
            if missing:
                raise CommandError(
                    f"Unknown permissions for {definition.custom_role_id}: {', '.join(missing)}"
                )
            RolePermissionMapping.objects.filter(role=role).delete()
            RolePermissionMapping.objects.bulk_create(
                [
                    RolePermissionMapping(role=role, permission_id=known_permissions[name])
                    for name in dict.fromkeys(definition.permission_names)
                ]
            )
            result[definition.custom_role_id] = role
        return result

    @staticmethod
    def _resolve_workspaces(scope, primary, business, all_workspaces):
        if scope == "primary":
            return [primary]
        if scope == "business":
            return [business]
        return all_workspaces

    @staticmethod
    def _replace_role_bindings(user, definition, workspaces, custom_roles):
        WorkspaceUserRoleMapping.objects.filter(user=user).delete()
        bindings = []
        for workspace in workspaces:
            if definition.bind_base_role:
                bindings.append(
                    WorkspaceUserRoleMapping(
                        workspace=workspace,
                        role_id=definition.base_role,
                        user=user,
                    )
                )
            for additional_role in definition.additional_roles:
                bindings.append(
                    WorkspaceUserRoleMapping(
                        workspace=workspace,
                        role_id=additional_role,
                        user=user,
                    )
                )
            if definition.custom_role_id:
                bindings.append(
                    WorkspaceUserRoleMapping(
                        workspace=workspace,
                        role=custom_roles[definition.custom_role_id],
                        user=user,
                    )
                )
        WorkspaceUserRoleMapping.objects.bulk_create(bindings)

    @staticmethod
    def _replace_resource_permissions(user, workspaces, access):
        workspace_ids = [workspace.id for workspace in workspaces]
        WorkspaceUserResourcePermission.objects.filter(
            user=user,
            workspace_id__in=workspace_ids,
        ).delete()
        if access is None:
            return

        from application.models import Application, ApplicationFolder
        from knowledge.models import Knowledge, KnowledgeFolder
        from models_provider.models import Model
        from tools.models import Tool, ToolFolder

        permissions = (
            [ResourcePermission.VIEW, ResourcePermission.MANAGE]
            if access == ResourcePermission.MANAGE
            else [ResourcePermission.VIEW]
        )
        instances = []
        for workspace in workspaces:
            resources = {
                AuthTargetType.APPLICATION: [workspace.id]
                + list(
                    Application.objects.filter(workspace_id=workspace.id).values_list("id", flat=True)
                )
                + list(
                    ApplicationFolder.objects.filter(workspace_id=workspace.id)
                    .exclude(id=workspace.id)
                    .values_list("id", flat=True)
                ),
                AuthTargetType.KNOWLEDGE: [workspace.id]
                + list(Knowledge.objects.filter(workspace_id=workspace.id).values_list("id", flat=True))
                + list(
                    KnowledgeFolder.objects.filter(workspace_id=workspace.id)
                    .exclude(id=workspace.id)
                    .values_list("id", flat=True)
                ),
                AuthTargetType.TOOL: [workspace.id]
                + list(Tool.objects.filter(workspace_id=workspace.id).values_list("id", flat=True))
                + list(
                    ToolFolder.objects.filter(workspace_id=workspace.id)
                    .exclude(id=workspace.id)
                    .values_list("id", flat=True)
                ),
                AuthTargetType.MODEL: list(
                    Model.objects.filter(workspace_id=workspace.id).values_list("id", flat=True)
                ),
            }
            for target_type, target_ids in resources.items():
                for target_id in dict.fromkeys(str(item) for item in target_ids):
                    instances.append(
                        WorkspaceUserResourcePermission(
                            workspace_id=workspace.id,
                            user=user,
                            auth_target_type=target_type,
                            target=target_id,
                            auth_type=ResourceAuthType.RESOURCE_PERMISSION_GROUP,
                            permission_list=permissions,
                        )
                    )
        WorkspaceUserResourcePermission.objects.bulk_create(instances)

    @staticmethod
    def _clear_auth_cache(user):
        permission_version, permission_get_key = Cache_Version.PERMISSION_LIST.value
        role_version, role_get_key = Cache_Version.ROLE_LIST.value
        cache.delete(permission_get_key(str(user.id)), version=permission_version)
        cache.delete(role_get_key(str(user.id)), version=role_version)

    @staticmethod
    def _new_password():
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz2345689-_!@#$%&*+="
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(18))
            if (
                any(char.islower() for char in password)
                and any(char.isupper() or char.isdigit() for char in password)
                and any(char in "-_!@#$%^&*`~.()+=" for char in password)
            ):
                return password

    @staticmethod
    def _write_credentials(path, credentials):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(path.parent, 0o700)
        lines = [
            "# 本地演示账号凭据（禁止提交仓库）",
            "# 首次登录后如需长期保留，请立即修改密码。",
            "",
        ]
        for definition, password, workspaces in credentials:
            lines.extend(
                [
                    f"角色：{definition.title}",
                    f"用户名：{definition.username}",
                    f"密码：{password}",
                    f"工作空间：{', '.join(workspace.name for workspace in workspaces)}",
                    "",
                ]
            )
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write("\n".join(lines))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
