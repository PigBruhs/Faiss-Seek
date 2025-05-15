import { createRouter, createWebHistory } from 'vue-router';
import axios from 'axios';

// 引入路由组件
import Home from'../components/Home.vue';
// 定义路由
const routes = [
  {
    path: '/',
    component:Home,
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;