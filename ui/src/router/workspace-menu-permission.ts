import { PermissionConst, RoleConst } from '@/utils/permission/data'
import type { Permission } from '@/utils/permission/type'

/**
 * A workspace menu is visible to the built-in administrators or to a custom
 * role that has explicitly been granted the corresponding menu permission.
 */
export function workspaceMenuPermission(permission: Permission) {
  return [
    RoleConst.ADMIN,
    RoleConst.WORKSPACE_MANAGE.getWorkspaceRole,
    permission.getWorkspacePermission,
    permission.getWorkspacePermissionWorkspaceManageRole,
  ]
}

export const workspaceMenuPermissions = {
  marketingScenario: workspaceMenuPermission(PermissionConst.MARKETING_SCENARIO_READ),
  marketingCampaign: workspaceMenuPermission(PermissionConst.MARKETING_CAMPAIGN_READ),
  marketingTask: workspaceMenuPermission(PermissionConst.MARKETING_TASK_READ),
  recommendationEngine: workspaceMenuPermission(PermissionConst.RECOMMENDATION_ENGINE_READ),
  marketingOperations: workspaceMenuPermission(PermissionConst.MARKETING_OPERATIONS_READ),
  marketingQuality: workspaceMenuPermission(PermissionConst.MARKETING_QUALITY_READ),
  analysisReport: workspaceMenuPermission(PermissionConst.ANALYSIS_REPORT_READ),
  metricOperations: workspaceMenuPermission(PermissionConst.METRIC_OPERATIONS_READ),
  platformMonitoring: workspaceMenuPermission(PermissionConst.PLATFORM_MONITORING_READ),
  apiOrchestration: workspaceMenuPermission(PermissionConst.API_ORCHESTRATION_READ),
  eventOrchestration: workspaceMenuPermission(PermissionConst.EVENT_ORCHESTRATION_READ),
  resourceCoordination: workspaceMenuPermission(PermissionConst.RESOURCE_COORDINATION_READ),
  ivrSimulator: workspaceMenuPermission(PermissionConst.IVR_SIMULATOR_READ),
  rehearsal: workspaceMenuPermission(PermissionConst.REHEARSAL_READ),
}
