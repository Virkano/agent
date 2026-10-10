<template>
  <el-dropdown trigger="click" placement="bottom-start" @command="navigate">
    <button
      type="button"
      class="menu-group-container border-r-6"
      :class="{ active: isActive }"
      :aria-current="isActive ? 'page' : undefined"
      :aria-label="`${title}菜单`"
      :title="title"
    >
      <div class="title flex align-center">
        <AppIcon :iconName="activeIcon" class="menu-icon" />
        <span class="title-text">{{ title }}</span>
        <el-icon class="menu-arrow"><ArrowDown /></el-icon>
      </div>
    </button>
    <template #dropdown>
      <el-dropdown-menu class="top-menu-dropdown">
        <el-dropdown-item
          v-for="menu in menus"
          :key="menu.path"
          :command="menu.path"
          :class="{ 'is-current': isMenuActive(menu) }"
        >
          <AppIcon
            :iconName="isMenuActive(menu) ? menu.meta?.iconActive || menu.meta?.icon : menu.meta?.icon"
            class="group-item-icon"
          />
          <span class="group-item-title">{{ translateTitle(menu.meta?.title as string) }}</span>
          <el-icon v-if="isMenuActive(menu)" class="current-icon"><Check /></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDown, Check } from '@element-plus/icons-vue'
import { useRoute, useRouter, type RouteRecordRaw } from 'vue-router'
import { i18n } from '@/locales'

const { title, icon, iconActive, menus } = defineProps<{
  title: string
  icon: string
  iconActive?: string
  menus: RouteRecordRaw[]
}>()

const route = useRoute()
const router = useRouter()

const currentMenuPath = computed(() => (route.meta.activeMenu as string | undefined) || route.path)
const isActive = computed(() => menus.some((menu) => menu.path === currentMenuPath.value))
const activeIcon = computed(() => (isActive.value ? iconActive || icon : icon))
const hasTranslation = i18n.global.te as unknown as (key: string) => boolean
const translate = i18n.global.t as unknown as (key: string) => string

function translateTitle(title?: string) {
  if (!title) return ''
  return hasTranslation(title) ? translate(title) : title
}

function isMenuActive(menu: RouteRecordRaw) {
  return menu.path === currentMenuPath.value
}

function navigate(path: string) {
  if (path !== currentMenuPath.value) router.push(path)
}
</script>

<style lang="scss" scoped>
.menu-group-container {
  position: relative;
  height: 36px;
  padding: 0 11px;
  border: 0;
  color: var(--el-text-color-primary);
  background: transparent;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition:
    color 160ms ease,
    background-color 160ms ease,
    box-shadow 160ms ease;

  .menu-icon {
    flex: 0 0 auto;
    margin-right: 6px;
    font-size: 17px;
  }

  &:hover {
    background-color: rgba(var(--el-text-color-primary-rgb), 0.1);
  }

  &:focus-visible {
    outline: 2px solid var(--el-color-primary-light-5);
    outline-offset: 2px;
  }

  &.active {
    background-color: #fff;
    box-shadow: 0 2px 6px rgba(var(--el-text-color-primary-rgb), 0.14);

    .title {
      color: var(--el-color-primary);
    }
  }
}

.menu-arrow {
  margin-left: 4px;
  font-size: 11px;
  transition: transform 160ms ease;
}

:deep(.el-tooltip__trigger[aria-expanded='true']) .menu-arrow {
  transform: rotate(180deg);
}

.group-item-icon {
  flex: 0 0 auto;
  margin-right: 9px;
  font-size: 17px;
}

.group-item-title {
  flex: 1;
}

.current-icon {
  margin-left: 16px;
  font-size: 14px;
}

@media (max-width: 1080px) {
  .title-text {
    display: none;
  }
}
</style>

<style lang="scss">
.top-menu-dropdown .el-dropdown-menu__item {
  min-width: 188px;
  padding: 10px 14px;
}

.top-menu-dropdown {
  max-height: min(440px, calc(100vh - 88px));
  overflow-y: auto;
}

.top-menu-dropdown .el-dropdown-menu__item.is-current {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
</style>
