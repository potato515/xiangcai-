<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-left">
        <div class="brand">
          <img src="@/assets/logo.svg" alt="logo" class="brand-logo" />
          <h1 class="brand-title">香菜工作台</h1>
          <p class="brand-desc">多平台内容自动化发布系统</p>
        </div>
        <div class="features">
          <div class="feature-item">
            <icon-file class="feature-icon" />
            <span>文章全生命周期管理</span>
          </div>
          <div class="feature-item">
            <icon-search class="feature-icon" />
            <span>百家号信息流标题采集</span>
          </div>
          <div class="feature-item">
            <icon-user class="feature-icon" />
            <span>5平台账号统一管理</span>
          </div>
          <div class="feature-item">
            <icon-command class="feature-icon" />
            <span>AI指令队列实时监控</span>
          </div>
        </div>
      </div>

      <div class="login-right">
        <div class="login-form-wrapper">
          <h2 class="login-title">欢迎登录</h2>
          <p class="login-subtitle">请输入您的账号信息</p>

          <a-form :model="form" :rules="rules" ref="formRef" @submit="handleLogin">
            <a-form-item field="username" label="用户名">
              <a-input v-model="form.username" placeholder="请输入用户名" size="large">
                <template #prefix><icon-user /></template>
              </a-input>
            </a-form-item>
            <a-form-item field="password" label="密码">
              <a-input-password v-model="form.password" placeholder="请输入密码" size="large" @press-enter="handleLogin">
                <template #prefix><icon-lock /></template>
              </a-input-password>
            </a-form-item>
            <a-form-item>
              <a-space>
                <a-checkbox v-model="form.remember">记住我</a-checkbox>
                <a-link>忘记密码？</a-link>
              </a-space>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" html-type="submit" size="large" long :loading="loading">
                登 录
              </a-button>
            </a-form-item>
          </a-form>

          <div class="login-tips">
            <a-alert type="info" :show-icon="false">
              <p>默认账号：admin / admin123（管理员）</p>
              <p>编辑员：editor / editor123</p>
            </a-alert>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconUser, IconLock, IconFile, IconSearch, IconCommand } from '@arco-design/web-vue/es/icon'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: true
})

const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }]
}

const handleLogin = async () => {
  const errors = await formRef.value?.validate()
  if (errors) return

  loading.value = true
  try {
    // 模拟登录（实际应调用 /api/auth/login）
    await new Promise(resolve => setTimeout(resolve, 800))

    if (form.username === 'admin' && form.password === 'admin123') {
      localStorage.setItem('xiangcai_token', 'token_admin')
      localStorage.setItem('xiangcai_user', JSON.stringify({ username: 'admin', name: '管理员', role: 'admin' }))
      Message.success('登录成功，欢迎管理员')
      router.push('/dashboard')
    } else if (form.username === 'editor' && form.password === 'editor123') {
      localStorage.setItem('xiangcai_token', 'token_editor')
      localStorage.setItem('xiangcai_user', JSON.stringify({ username: 'editor', name: '编辑员', role: 'editor' }))
      Message.success('登录成功，欢迎编辑员')
      router.push('/dashboard')
    } else {
      Message.error('用户名或密码错误')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  width: 900px;
  height: 560px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  overflow: hidden;
}
.login-left {
  width: 45%;
  background: linear-gradient(135deg, #165dff 0%, #4080ff 100%);
  padding: 40px 32px;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.brand { margin-bottom: 40px; }
.brand-logo { width: 48px; height: 48px; margin-bottom: 16px; }
.brand-title { font-size: 28px; font-weight: 700; margin: 0 0 8px; }
.brand-desc { font-size: 14px; opacity: 0.85; margin: 0; }
.features { flex: 1; display: flex; flex-direction: column; gap: 16px; }
.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.9;
}
.feature-icon { font-size: 20px; }
.login-right {
  width: 55%;
  padding: 48px 40px;
  display: flex;
  align-items: center;
}
.login-form-wrapper { width: 100%; }
.login-title { font-size: 24px; font-weight: 700; margin: 0 0 8px; }
.login-subtitle { font-size: 14px; color: var(--color-text-3); margin: 0 0 32px; }
.login-tips { margin-top: 24px; }
.login-tips p { margin: 4px 0; font-size: 12px; }
</style>
