import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const recommendationEngineRouter = {
  path: '/recommendation-engine',
  name: 'recommendation-engine',
  meta: {
    title: 'views.recommendationEngine.title',
    menu: true,
    permission: workspaceMenuPermissions.recommendationEngine,
    icon: 'Connection',
    group: 'workspace',
    order: 4.2,
  },
  redirect: '/recommendation-engine',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/recommendation-engine',
      name: 'recommendation-engine-index',
      meta: {
        title: 'views.recommendationEngine.title',
        activeMenu: '/recommendation-engine',
        sameRoute: 'recommendation-engine',
      },
      component: () => import('@/views/recommendation-engine/index.vue'),
      hidden: true,
    },
  ],
}

export default recommendationEngineRouter
