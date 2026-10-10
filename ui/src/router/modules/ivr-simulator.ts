import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const ivrSimulatorRouter = {
  path: '/ivr-simulator',
  name: 'ivr-simulator',
  meta: {
    title: 'views.ivrSimulator.title',
    menu: true,
    permission: workspaceMenuPermissions.ivrSimulator,
    icon: 'Headset',
    group: 'workspace',
    order: 6.2,
  },
  redirect: '/ivr-simulator',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/ivr-simulator',
      name: 'ivr-simulator-index',
      meta: {
        title: 'views.ivrSimulator.title',
        activeMenu: '/ivr-simulator',
        sameRoute: 'ivr-simulator',
      },
      component: () => import('@/views/ivr-simulator/index.vue'),
      hidden: true,
    },
  ],
}

export default ivrSimulatorRouter
