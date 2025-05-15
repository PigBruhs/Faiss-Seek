import './assets/main.css';
import { createApp } from 'vue';
import ArcoVue from '@arco-design/web-vue';
import App from './App.vue';
import '@arco-design/web-vue/dist/arco.css';
import router from './router/index.js'; // 引入路由配置文件

// 创建 Vue 应用实例
const app = createApp(App);

// 使用插件
app.use(ArcoVue);
app.use(router); // 正确注册路由

// 挂载应用
app.mount('#app');