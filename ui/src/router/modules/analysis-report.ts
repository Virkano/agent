import { workspaceMenuPermissions } from '@/router/workspace-menu-permission'

const analysisReportRouter = {
  path: '/analysis-report',
  name: 'analysis-report',
  meta: {
    title: 'AI 分析报告',
    menu: true,
    permission: workspaceMenuPermissions.analysisReport,
    icon: 'DataAnalysis',
    group: 'workspace',
    order: 5.5,
  },
  redirect: '/analysis-report',
  component: () => import('@/layout/layout-template/SimpleLayout.vue'),
  children: [
    {
      path: '/analysis-report',
      name: 'analysis-report-index',
      meta: {
        title: 'AI 分析报告',
        activeMenu: '/analysis-report',
        sameRoute: 'analysis-report',
      },
      component: () => import('@/views/analysis-report/index.vue'),
      hidden: true,
    },
  ],
}

export default analysisReportRouter
