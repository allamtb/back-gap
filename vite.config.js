import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 通过环境变量快速切换后端地址
// 使用方式：
// npm run dev              -> 默认使用远程 IP
// npm run dev:local        -> 使用 localhost
// VITE_BACKEND_HOST=xxx npm run dev -> 自定义地址

const backendHost = process.env.VITE_BACKEND_HOST || '16.163.163.204'
const backendPort = process.env.VITE_BACKEND_PORT || '8000'
const httpTarget = `http://${backendHost}:${backendPort}`
const wsTarget = `ws://${backendHost}:${backendPort}`

console.log(`🔗 代理后端地址: ${httpTarget}`)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // 允许远程访问，监听所有网络接口
    port: 5173, // 修改为你想要的端口号，例如 3000, 8080 等
    proxy: {
      '/health': {
        target: httpTarget,
        changeOrigin: true,
      },
      '/api': {
        target: httpTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: wsTarget,
        ws: true,
        changeOrigin: true,
        // 添加超时和错误处理配置
        timeout: 60000,
        // 配置 WebSocket 错误处理（静默处理连接中断错误）
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            // 只记录非 ECONNABORTED 的错误（连接中止是正常的）
            if (err.code !== 'ECONNABORTED' && err.code !== 'ECONNRESET') {
              console.error('WebSocket 代理错误:', err.message);
            }
          });
          proxy.on('close', () => {
            // 连接关闭是正常的，不需要记录
          });
        },
      }
    }
  }
})
