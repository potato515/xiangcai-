import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/BasicLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'icon-dashboard' }
      },
      {
        path: 'article',
        name: 'Article',
        component: () => import('@/views/article/list.vue'),
        meta: { title: '文章管理', icon: 'icon-file' }
      },
      {
        path: 'article/detail/:id',
        name: 'ArticleDetail',
        component: () => import('@/views/article/detail.vue'),
        meta: { title: '文章详情', hidden: true }
      },
      {
        path: 'article/batch-import',
        name: 'BatchImport',
        component: () => import('@/views/article/batch-import.vue'),
        meta: { title: '批量导入', hidden: true }
      },
      {
        path: 'article-generate',
        name: 'ArticleGenerate',
        component: () => import('@/views/article-generate/index.vue'),
        meta: { title: '文章生成', icon: 'icon-edit' }
      },
      {
        path: 'ai-config',
        name: 'AIConfig',
        component: () => import('@/views/ai-config/index.vue'),
        meta: { title: 'AI配置', icon: 'icon-settings' }
      },
      {
        path: 'title-spider',
        name: 'TitleSpider',
        component: () => import('@/views/title-spider/index.vue'),
        meta: { title: '标题采集', icon: 'icon-search' }
      },
      {
        path: 'account',
        name: 'Account',
        redirect: '/account/baijiahao',
        meta: { title: '账号管理', icon: 'icon-user' },
        children: [
          {
            path: 'baijiahao',
            name: 'BaijiahaoAccount',
            component: () => import('@/views/account/baijiahao.vue'),
            meta: { title: '百家号账号' }
          },
          {
            path: 'doubao',
            name: 'DoubaoAccount',
            component: () => import('@/views/account/doubao.vue'),
            meta: { title: '豆包账号' }
          },
          {
            path: 'yangdu',
            name: 'YangduAccount',
            component: () => import('@/views/account/yangdu.vue'),
            meta: { title: '仰度AI账号' }
          },
          {
            path: 'zhipu',
            name: 'ZhipuAccount',
            component: () => import('@/views/account/zhipu.vue'),
            meta: { title: '智谱AI账号' }
          },
          {
            path: 'yuanbao',
            name: 'YuanbaoAccount',
            component: () => import('@/views/account/yuanbao.vue'),
            meta: { title: '元宝账号' }
          }
        ]
      },
      {
        path: 'topic',
        name: 'Topic',
        component: () => import('@/views/topic/index.vue'),
        meta: { title: '话题管理', icon: 'icon-tag' }
      },
      {
        path: 'command',
        name: 'Command',
        component: () => import('@/views/command/index.vue'),
        meta: { title: '指令队列', icon: 'icon-order' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/logs/index.vue'),
        meta: { title: '日志监控', icon: 'icon-logs' }
      },
      {
        path: 'settings',
        name: 'Settings',
        redirect: '/settings/format',
        meta: { title: '系统设置', icon: 'icon-settings' },
        children: [
          {
            path: 'format',
            name: 'FormatSettings',
            component: () => import('@/views/settings/format.vue'),
            meta: { title: '排版设置' }
          },
          {
            path: 'export',
            name: 'ExportSettings',
            component: () => import('@/views/settings/export.vue'),
            meta: { title: '导出设置' }
          },
          {
            path: 'generate',
            name: 'GenerateSettings',
            component: () => import('@/views/settings/generate.vue'),
            meta: { title: '生成设置' }
          }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：检查登录状态
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 香菜工作台` : '香菜工作台'

  // 公开页面（登录页）不需要鉴权
  if (to.meta.public) {
    next()
    return
  }

  // 检查token
  const token = localStorage.getItem('xiangcai_token')
  if (!token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
