<template>
  <nav class="top-menu-container flex align-center h-full" aria-label="主导航">
    <MenuItem v-for="menu in directMenus" :key="menu.path" :menu="menu" />
    <MenuGroup
      v-for="group in menuGroups"
      :key="group.key"
      :title="group.title"
      :icon="group.icon"
      :icon-active="group.iconActive"
      :menus="group.menus"
    />
  </nav>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import type { RouteRecordRaw } from 'vue-router'
import { getChildRouteListByPathAndName } from '@/router/index'
import { hasPermission } from '@/utils/permission/index'
import MenuItem from './MenuItem.vue'
import MenuGroup from './MenuGroup.vue'

interface MenuGroupConfig {
  key: string
  title: string
  icon: string
  iconActive?: string
  paths: string[]
}

const directPaths = ['/home', '/application']
const groupConfigs: MenuGroupConfig[] = [
  {
    key: 'capability',
    title: 'AI 能力',
    icon: 'Connection',
    paths: ['/knowledge', '/model', '/tool', '/service-answer-review'],
  },
  {
    key: 'marketing',
    title: '营销业务',
    icon: 'Promotion',
    paths: ['/marketing-scenario', '/marketing-campaign', '/marketing-task', '/recommendation-engine'],
  },
  {
    key: 'operations',
    title: '运营分析',
    icon: 'DataAnalysis',
    paths: [
      '/marketing-operations',
      '/marketing-quality',
      '/analysis-report',
      '/metric-operations',
      '/platform-monitoring',
    ],
  },
  {
    key: 'orchestration',
    title: '调度与演练',
    icon: 'Operation',
    paths: [
      '/integration-orchestration',
      '/event-orchestration',
      '/resource-coordination',
      '/ivr-simulator',
      '/rehearsal',
    ],
  },
]

const topMenuList = computed<RouteRecordRaw[]>(() => {
  const menu = getChildRouteListByPathAndName('/', 'root').filter(
    (item) =>
      item.meta?.menu &&
      (item.meta.permission ? hasPermission(item.meta.permission as any, 'OR') : true),
  )
  menu.sort(
    (a, b) =>
      (a.meta ? (a.meta.order ? (a.meta.order as number) : 1) : 1) -
      (b.meta ? (b.meta.order ? (b.meta.order as number) : 1) : 1),
  )
  return menu
})

const groupedPaths = new Set(groupConfigs.flatMap((group) => group.paths))
const directMenus = computed(() =>
  directPaths.flatMap((path) => topMenuList.value.filter((menu) => menu.path === path)),
)

const menuGroups = computed(() => {
  const groups = groupConfigs
    .map((group) => ({
      ...group,
      menus: group.paths.flatMap((path) => topMenuList.value.filter((menu) => menu.path === path)),
    }))
    .filter((group) => group.menus.length)
  const ungrouped = topMenuList.value.filter(
    (menu) => !directPaths.includes(menu.path) && !groupedPaths.has(menu.path),
  )
  if (ungrouped.length) {
    groups.push({ key: 'more', title: '更多', icon: 'MoreFilled', menus: ungrouped, paths: [] })
  }
  return groups
})
</script>

<style lang="scss" scoped>
.top-menu-container {
  flex: 1 1 auto;
  min-width: 0;
  justify-content: center;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
  white-space: nowrap;

  &::-webkit-scrollbar {
    display: none;
  }
}
</style>
