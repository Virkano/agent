import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const metricFoundationRouter = {
  path: '/metric-operations',
  name: 'metric-operations',
  meta: {
    title: '指标预警中心',
    menu: true,
    permission: workspaceMenuPermissions.metricOperations,
    icon: 'DataAnalysis',
    group: 'workspace',
    order: 5.69,
  },
  redirect: '/metric-operations',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/metric-operations',
      name: 'metric-operations-index',
      meta: {
        title: '指标预警中心',
        activeMenu: '/metric-operations',
        sameRoute: 'metric-operations',
      },
      component: () => import('@/views/metric-foundation/index.vue'),
      hidden: true,
    },
  ],
}

export default metricFoundationRouter
