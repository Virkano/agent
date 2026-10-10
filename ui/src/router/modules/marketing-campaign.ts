import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const marketingCampaignRouter = {
  path: '/marketing-campaign',
  name: 'marketing-campaign',
  meta: {
    title: '营销活动库',
    menu: true,
    permission: workspaceMenuPermissions.marketingCampaign,
    icon: 'Promotion',
    group: 'workspace',
    order: 4,
  },
  redirect: '/marketing-campaign',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/marketing-campaign',
      name: 'marketing-campaign-index',
      meta: {
        title: '营销活动库',
        activeMenu: '/marketing-campaign',
        sameRoute: 'marketing-campaign',
      },
      component: () => import('@/views/marketing-campaign/index.vue'),
      hidden: true,
    },
  ],
}
export default marketingCampaignRouter
