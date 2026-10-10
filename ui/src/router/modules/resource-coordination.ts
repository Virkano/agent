import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const resourceCoordinationRouter = {
  path: '/resource-coordination',
  name: 'resource-coordination',
  meta: {
    title: '资源协调中心',
    menu: true,
    permission: workspaceMenuPermissions.resourceCoordination,
    icon: 'Operation',
    group: 'workspace',
    order: 5.65,
  },
  redirect: '/resource-coordination',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/resource-coordination',
      name: 'resource-coordination-index',
      meta: {
        title: '资源协调中心',
        activeMenu: '/resource-coordination',
        sameRoute: 'resource-coordination',
      },
      component: () => import('@/views/resource-coordination/index.vue'),
      hidden: true,
    },
  ],
}

export default resourceCoordinationRouter
