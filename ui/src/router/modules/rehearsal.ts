import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const rehearsalRouter = {
  path: '/rehearsal',
  name: 'rehearsal',
  meta: {
    title: 'views.rehearsal.title',
    menu: true,
    permission: workspaceMenuPermissions.rehearsal,
    icon: 'VideoPlay',
    group: 'workspace',
    order: 6.3,
  },
  redirect: '/rehearsal',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/rehearsal',
      name: 'rehearsal-index',
      meta: {
        title: 'views.rehearsal.title',
        activeMenu: '/rehearsal',
        sameRoute: 'rehearsal',
      },
      component: () => import('@/views/rehearsal/index.vue'),
      hidden: true,
    },
  ],
}

export default rehearsalRouter
