import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const apiOrchestrationRouter = {
  path: '/integration-orchestration',
  name: 'api-orchestration',
  meta: {
    title: 'API 编排与晓搭',
    menu: true,
    permission: workspaceMenuPermissions.apiOrchestration,
    icon: 'Connection',
    group: 'workspace',
    order: 5.68,
  },
  redirect: '/integration-orchestration',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/integration-orchestration',
      name: 'api-orchestration-index',
      meta: {
        title: 'API 编排与晓搭',
        activeMenu: '/integration-orchestration',
        sameRoute: 'api-orchestration',
      },
      component: () => import('@/views/api-orchestration/index.vue'),
      hidden: true,
    },
  ],
}

export default apiOrchestrationRouter
