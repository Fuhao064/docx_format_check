import { createRouter, createWebHistory } from 'vue-router'
import ModelManager from '../components/ModelManager.vue'

const routes = [
  {
    path: '/models',
    name: 'ModelManager',
    component: ModelManager
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router