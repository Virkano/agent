import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const marketingOperationsRouter = {
  path: '/marketing-operations',
  name: 'marketing-operations',
  meta: {
    title: '运营监控',
    menu: true,
    permission: workspaceMenuPermissions.marketingOperations,
    icon: 'TrendCharts',
    group: 'workspace',
    order: 5,
  },
  redirect: '/marketing-operations',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/marketing-operations',
      name: 'marketing-operations-index',
      meta: {
        title: '运营监控',
        activeMenu: '/marketing-operations',
        sameRoute: 'marketing-operations',
      },
      component: () => import('@/views/marketing-operations/index.vue'),
      hidden: true,
    },
  ],
}

export default marketingOperationsRouter
