import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const eventOrchestrationRouter = {
  path: '/event-orchestration',
  name: 'event-orchestration',
  meta: {
    title: '事件任务编排',
    menu: true,
    permission: workspaceMenuPermissions.eventOrchestration,
    icon: 'Share',
    group: 'workspace',
    order: 5.64,
  },
  redirect: '/event-orchestration',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/event-orchestration',
      name: 'event-orchestration-index',
      meta: {
        title: '事件任务编排',
        activeMenu: '/event-orchestration',
        sameRoute: 'event-orchestration',
      },
      component: () => import('@/views/event-orchestration/index.vue'),
      hidden: true,
    },
  ],
}

export default eventOrchestrationRouter
