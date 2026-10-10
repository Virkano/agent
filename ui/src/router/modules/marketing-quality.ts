import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const marketingQualityRouter = {
  path: '/marketing-quality',
  name: 'marketing-quality',
  meta: {
    title: '对话质检',
    menu: true,
    permission: workspaceMenuPermissions.marketingQuality,
    icon: 'CircleCheck',
    group: 'workspace',
    order: 6,
  },
  redirect: '/marketing-quality',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/marketing-quality',
      name: 'marketing-quality-index',
      meta: {
        title: '对话质检',
        activeMenu: '/marketing-quality',
        sameRoute: 'marketing-quality',
      },
      component: () => import('@/views/marketing-quality/index.vue'),
      hidden: true,
    },
  ],
}

export default marketingQualityRouter
