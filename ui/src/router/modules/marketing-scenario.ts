import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const marketingScenarioRouter = {
  path: '/marketing-scenario',
  name: 'marketing-scenario',
  meta: {
    title: '营销场景',
    menu: true,
    permission: workspaceMenuPermissions.marketingScenario,
    icon: 'Compass',
    group: 'workspace',
    order: 3,
  },
  redirect: '/marketing-scenario',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/marketing-scenario',
      name: 'marketing-scenario-index',
      meta: { title: '营销场景', activeMenu: '/marketing-scenario', sameRoute: 'marketing-scenario' },
      component: () => import('@/views/marketing-scenario/index.vue'),
      hidden: true,
    },
  ],
}

export default marketingScenarioRouter
