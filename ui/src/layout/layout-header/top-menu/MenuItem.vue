<template>
  <button
    type="button"
    class="menu-item-container h-full border-r-6"
    :class="{ active: isActive }"
    :aria-current="isActive ? 'page' : undefined"
    :aria-label="translateTitle(menu.meta?.title as string)"
    :title="translateTitle(menu.meta?.title as string)"
    @click="router.push({ name: menu.name })"
  >
    <div class="title flex align-center">
      <AppIcon
        :iconName="isActive ? menu.meta?.iconActive || menu.meta?.icon : menu?.meta?.icon"
        class="menu-icon"
      />
      <span class="title-text">{{ translateTitle(menu.meta?.title as string) }}</span>
    </div>
  </button>
</template>
<script setup lang="ts">
import { useRouter, useRoute, type RouteRecordRaw } from 'vue-router'
import { computed } from 'vue'
import { i18n } from '@/locales'

const router = useRouter()
const route = useRoute()

const props = defineProps<{
  menu: RouteRecordRaw
}>()
const hasTranslation = i18n.global.te as unknown as (key: string) => boolean
const translate = i18n.global.t as unknown as (key: string) => string

function translateTitle(title?: string) {
  if (!title) return ''
  return hasTranslation(title) ? translate(title) : title
}

const isActive = computed(() => {
  const { name, path, meta } = route
  return (name == props.menu.name && path == props.menu.path) || meta?.activeMenu == props.menu.path
})
</script>
<style lang="scss" scoped>
.menu-item-container {
  height: 36px;
  border: 0;
  color: var(--el-text-color-primary);
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  font-family: inherit;
  position: relative;
  padding: 0 12px;
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
    background-color: #ffffff;
    box-shadow: 0 2px 6px rgba(var(--el-text-color-primary-rgb), 0.14);

    .title {
      color: var(--el-color-primary);
    }
  }

  .title-text {
    @media (max-width: 1080px) {
      display: none;
    }
  }
}
</style>
