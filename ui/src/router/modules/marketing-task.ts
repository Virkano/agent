import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const marketingTaskRouter = {
  path: '/marketing-task',
  name: 'marketing-task',
  meta: {
    title: '营销任务',
    menu: true,
    permission: workspaceMenuPermissions.marketingTask,
    icon: 'List',
    group: 'workspace',
    order: 4,
  },
  redirect: '/marketing-task',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/marketing-task',
      name: 'marketing-task-index',
      meta: { title: '营销任务', activeMenu: '/marketing-task', sameRoute: 'marketing-task' },
      component: () => import('@/views/marketing-task/index.vue'),
      hidden: true,
    },
  ],
}

export default marketingTaskRouter
