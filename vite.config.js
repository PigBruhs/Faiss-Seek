import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'


// 自动导入vue中hook reactive ref等
import AutoImport from "unplugin-auto-import/vite"
//自动导入ui-组件 比如说ant-design-vue  element-plus等
import Components from 'unplugin-vue-components/vite'
import { ArcoResolver } from 'unplugin-vue-components/resolvers';
import { createStyleImportPlugin } from 'vite-plugin-style-import'
import VueDevTools from 'vite-plugin-vue-devtools'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    VueDevTools(),
    vue(),
    AutoImport({
      //安装两行后你会发现在组件中不用再导入ref，reactive等
      imports: ['vue', 'vue-router'],
      //存放的位置
      dts: "src/auto-import.d.ts",
      resolvers: [ArcoResolver()],
    }),
    Components({
      // 引入组件的,包括自定义组件
      // 存放的位置
      dts: "src/components.d.ts",
      resolvers: [
        ArcoResolver({
          sideEffect: true
        })
      ]
    }),
    createStyleImportPlugin({
      libs: [
        {
          libraryName: '@arco-design/web-vue',
          esModule: true,
          resolveStyle: (name) => {
            if (name.startsWith('icon')) {
              return ''; // 不加载样式
            }
            return `@arco-design/web-vue/es/${name}/style/index.css`;
          },
        }
      ]
    })
  ],
// vite.config.js
  server: {
    host: '127.0.0.1',
    port: 14514,
    proxy: {
      '/reverse': {
        target: 'http://localhost:19198', // 后端服务地址
        changeOrigin: true,
        pathRewrite: { '^/reverse': '' },
      },
    },
  },
});