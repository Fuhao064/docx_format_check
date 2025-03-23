// 确保路由文件路径和导出方式正确
import { createRouter, createWebHistory } from 'vue-router'

// 导入页面组件
import Main from '../views/Main.vue'
import Models from '../views/Models.vue'
import Help from '../views/Help.vue'
import Format from '../views/Format.vue'
import About from '../views/About.vue'  

// 定义路由
const routes = [
  { path: '/', name: 'home', component: Main },
  { path: '/models', name: 'models', component: () => import('../views/Models.vue') },
  { path: '/format', name: 'format', component: () => import('../views/Format.vue') },
  { path: '/help', name: 'help', component: () => import('../views/Help.vue') },
  { path: '/about', name: 'about', component: () => import('../views/About.vue') },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router