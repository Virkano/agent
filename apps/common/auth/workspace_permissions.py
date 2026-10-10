from common.constants.permission_constants import PermissionConstants, RoleConstants


def workspace_menu_permissions(permission: PermissionConstants):
    """Return the common access rule for one assignable workspace menu."""

    return (
        RoleConstants.ADMIN,
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
        permission.get_workspace_permission(),
        permission.get_workspace_permission_workspace_manage_role(),
    )
