import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const platformMonitoringRouter = {
  path: '/platform-monitoring',
  name: 'platform-monitoring',
  meta: {
    title: 'views.platformMonitoring.title',
    menu: true,
    permission: workspaceMenuPermissions.platformMonitoring,
    icon: 'Monitor',
    group: 'workspace',
    order: 5.7,
  },
  redirect: '/platform-monitoring',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/platform-monitoring',
      name: 'platform-monitoring-index',
      meta: {
        title: 'views.platformMonitoring.title',
        activeMenu: '/platform-monitoring',
        sameRoute: 'platform-monitoring',
      },
      component: () => import('@/views/platform-monitoring/index.vue'),
      hidden: true,
    },
  ],
}

export default platformMonitoringRouter
