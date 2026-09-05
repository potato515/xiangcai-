import axios from 'axios'
import { Message } from '@arco-design/web-vue'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

request.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 静默模式：不弹出全局错误提示（用于轮询等后台请求）
    if (!error.config?.silent) {
      Message.error(error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
