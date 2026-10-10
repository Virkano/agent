import { PermissionConst, RoleConst } from '@/utils/permission/data'

const serviceAnswerReviewRouter = {
  path: '/service-answer-review',
  name: 'service-answer-review',
  meta: {
    title: '服务助手复核',
    menu: true,
    permission: [
      RoleConst.ADMIN,
      RoleConst.WORKSPACE_MANAGE.getWorkspaceRole,
      PermissionConst.APPLICATION_CHAT_LOG_READ.getWorkspacePermission,
    ],
    icon: 'CircleCheck',
    group: 'workspace',
    order: 3.8,
  },
  redirect: '/service-answer-review',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/service-answer-review',
      name: 'service-answer-review-index',
      meta: {
        title: '服务助手复核',
        activeMenu: '/service-answer-review',
        sameRoute: 'service-answer-review',
      },
      component: () => import('@/views/service-answer-review/index.vue'),
      hidden: true,
    },
  ],
}

export default serviceAnswerReviewRouter
