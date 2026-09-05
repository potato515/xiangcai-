<template>
  <a-layout class="basic-layout">
    <a-layout-sider
      :width="220"
      :collapsed="collapsed"
      :collapsible="true"
      @collapse="handleCollapse"
      breakpoint="xl"
      hide-trigger
    >
      <div class="logo">
        <img src="@/assets/logo.svg" alt="logo" class="logo-img" v-if="!collapsed" />
        <span class="logo-text" v-if="!collapsed">香菜工作台</span>
        <span class="logo-text-mini" v-else>香</span>
      </div>
      <a-menu
        :default-selected-keys="[activeMenu]"
        :default-open-keys="openKeys"
        @menu-item-click="handleMenuClick"
      >
        <template v-for="item in menuList" :key="item.path">
          <a-menu-item v-if="!item.children" :key="item.path">
            <component :is="item.icon" />
            <span>{{ item.title }}</span>
          </a-menu-item>
          <a-sub-menu v-else :key="item.path">
            <template #title>
              <component :is="item.icon" />
              <span>{{ item.title }}</span>
            </template>
            <a-menu-item v-for="child in item.children" :key="child.path">
              {{ child.title }}
            </a-menu-item>
          </a-sub-menu>
        </template>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="layout-header">
        <div class="header-left">
          <a-breadcrumb>
            <a-breadcrumb-item v-for="(item, idx) in breadcrumbs" :key="idx">
              {{ item }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>
        <div class="header-right">
          <a-tooltip :content="appStore.darkMode ? '切换到浅色模式' : '切换到深色模式'">
            <a-button type="text" :icon="appStore.darkMode ? IconSun : IconMoon" @click="appStore.toggleDark" />
          </a-tooltip>
          <a-tooltip content="折叠侧边栏">
            <a-button type="text" :icon="collapsed ? IconMenuUnfold : IconMenuFold" @click="appStore.toggleSidebar" />
          </a-tooltip>
          <a-tag color="green" class="status-tag">
            <a-dot type="success" /> 服务运行中
          </a-tag>
          <a-dropdown>
            <a-avatar style="background-color: #165dff; cursor: pointer">
              {{ currentUser.name.charAt(0) }}
            </a-avatar>
            <template #content>
              <div style="padding:8px 16px;border-bottom:1px solid var(--color-border-2);margin-bottom:4px">
                <div style="font-weight:600">{{ currentUser.name }}</div>
                <div style="font-size:12px;color:var(--color-text-3)">{{ currentUser.role === 'admin' ? '管理员' : '编辑员' }}</div>
              </div>
              <a-doption>个人中心</a-doption>
              <a-doption>系统设置</a-doption>
              <a-doption @click="handleLogout" style="color:#f53f3f">退出登录</a-doption>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content class="layout-content">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </a-layout-content>

      <a-layout-footer class="layout-footer">
        香菜工作台 v1.0.0 · 多平台内容自动化发布系统
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import {
  IconDashboard,
  IconFile,
  IconSearch,
  IconUser,
  IconTag,
  IconCommand,
  IconSettings,
  IconMoon,
  IconSun,
  IconMenuFold,
  IconMenuUnfold,
  IconBug
} from '@arco-design/web-vue/es/icon'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const { sidebarCollapsed: collapsed } = storeToRefs(appStore)

const iconMap = {
  'icon-dashboard': IconDashboard,
  'icon-file': IconFile,
  'icon-search': IconSearch,
  'icon-user': IconUser,
  'icon-tag': IconTag,
  'icon-order': IconCommand,
  'icon-logs': IconBug,
  'icon-settings': IconSettings
}

const menuList = computed(() => {
  const buildMenu = (routes, parentPath = '') => {
    if (!routes) return []
    return routes
      .filter(r => !r.meta?.hidden)
      .map(r => {
        // 确保路径以 / 开头，避免相对路径拼接问题
        let fullPath
        if (parentPath) {
          fullPath = `${parentPath}/${r.path}`.replace(/\/+/g, '/')
        } else {
          fullPath = r.path.startsWith('/') ? r.path : `/${r.path}`
        }
        return {
          path: fullPath,
          title: r.meta?.title || '',
          icon: iconMap[r.meta?.icon] || IconDashboard,
          children: r.children ? buildMenu(r.children.filter(c => !c.meta?.hidden), fullPath) : null
        }
      })
  }
  const rootRoute = router.options.routes.find(r => r.path === '/')
  return buildMenu(rootRoute ? rootRoute.children : [])
})

const activeMenu = computed(() => route.path)

const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('xiangcai_user') || '{"name":"香","role":"admin"}')
  } catch {
    return { name: '香', role: 'admin' }
  }
})

const handleLogout = () => {
  localStorage.removeItem('xiangcai_token')
  localStorage.removeItem('xiangcai_user')
  router.push('/login')
}
const openKeys = computed(() => {
  const paths = route.path.split('/').filter(Boolean)
  return paths.length > 1 ? ['/' + paths[0]] : []
})

const breadcrumbs = computed(() => {
  return route.matched
    .filter(r => r.meta?.title)
    .map(r => r.meta.title)
})

const handleCollapse = (val) => {
  appStore.sidebarCollapsed = val
}

const handleMenuClick = (key) => {
  router.push(key)
}

watch(() => route.path, () => {
  // 路由变化时菜单状态自动更新
})
</script>

<style scoped>
.basic-layout {
  height: 100vh;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid var(--color-border-2);
}

.logo-img {
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
}

.logo-text-mini {
  font-size: 20px;
  font-weight: 700;
  color: #165dff;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border-2);
  height: 60px;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.layout-content {
  margin: 16px;
  padding: 20px;
  background: var(--color-bg-2);
  border-radius: 4px;
  overflow-y: auto;
  min-height: 0;
}

.layout-footer {
  text-align: center;
  color: var(--color-text-3);
  font-size: 12px;
  padding: 12px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:deep(.arco-layout-sider-light) {
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
}

:deep(.arco-menu-light) {
  border-right: none;
}
</style>
