import { createRouter, createWebHistory } from 'vue-router';

// 引入路由组件
import Home from'../components/Home.vue';
import Login from '../components/LoginPage.vue';
import Register from '../components/RegisterPage.vue';
// 定义路由
const routes = [
  {
    path: '/',
    redirect: '/Login', // 默认重定向到登录页面
  },
  {
    path:'/Login',
    component: Login,
  },
  {
    path: '/Register',
    component: Register,
  },
  {
    path: '/Home',
    component: Home,
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;