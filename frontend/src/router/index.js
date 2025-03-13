// 确保路由文件路径和导出方式正确
import { createRouter, createWebHistory } from 'vue-router'

// 导入页面组件
import Home from '../views/Home.vue'
import Models from '../views/Models.vue'
import Help from '../views/Help.vue'
import Format from '../views/Format.vue'
import About from '../views/About.vue'
import Settings from '../views/Settings.vue'

// 定义路由
const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/models', name: 'models', component: Models },
  { path: '/format', name: 'format', component: Format },
  { path: '/help', name: 'help', component: Help },
  { path: '/about', name: 'about', component: About },
  { path: '/settings', name: 'settings', component: Settings }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router