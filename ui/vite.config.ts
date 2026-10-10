import { fileURLToPath, URL } from 'node:url'
import type { ProxyOptions } from 'vite'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import DefineOptions from 'unplugin-vue-define-options/vite'
import path from 'path'
import { createHtmlPlugin } from 'vite-plugin-html'
import fs from 'fs'
// import vueDevTools from 'vite-plugin-vue-devtools'
const envDir = './env'
// 自定义插件：重命名入口文件
const renameHtmlPlugin = (outDir: string, entry: string) => {
  return {
    name: 'rename-html',
    closeBundle: () => {
      const buildDir = path.resolve(__dirname, outDir)
      const oldFile = path.join(buildDir, entry)
      const newFile = path.join(buildDir, 'index.html')

      // 检查文件是否存在
      if (fs.existsSync(oldFile)) {
        // 删除已存在的 index.html
        if (fs.existsSync(newFile)) {
          fs.unlinkSync(newFile)
        }
        // 重命名文件
        fs.renameSync(oldFile, newFile)
      }
    },
  }
}
const localBasePathFallbackPlugin = (basePath: string, entry: string) => {
  const normalizedBasePath = basePath.replace(/\/$/, '')
  const adminRoutePrefixes = [
    '/application',
    '/knowledge',
    '/tool',
    '/system',
    '/home',
    '/ivr-simulator',
    '/rehearsal',
    '/event-orchestration',
    '/resource-coordination',
    '/integration-orchestration',
    '/permission',
    '/no-permission',
  ]
  return {
    name: 'local-base-path-fallback',
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        const [pathname, search = ''] = (req.url || '').split('?')
        if (
          normalizedBasePath === '/admin' &&
          adminRoutePrefixes.some(
            (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
          )
        ) {
          res.statusCode = 302
          res.setHeader('Location', `${normalizedBasePath}${pathname}${search ? `?${search}` : ''}`)
          res.end()
          return
        }
        if (
          normalizedBasePath === '/admin' &&
          (pathname === '/chat' || pathname.startsWith('/chat/')) &&
          !pathname.startsWith('/chat/api') &&
          !pathname.startsWith('/chat/api-doc') &&
          !pathname.includes('.')
        ) {
          req.url = `/chat.html${search ? `?${search}` : ''}`
          next()
          return
        }
        if (!pathname.startsWith(`${normalizedBasePath}/`)) {
          next()
          return
        }
        if (
          pathname.startsWith(`${normalizedBasePath}/api`) ||
          pathname.startsWith(`${normalizedBasePath}/api-doc`)
        ) {
          next()
          return
        }
        if (pathname.includes('.')) {
          req.url = `${pathname.replace(normalizedBasePath, '')}${search ? `?${search}` : ''}`
          next()
          return
        }
        req.url = `/${entry}${search ? `?${search}` : ''}`
        next()
      })
    },
  }
}
// https://vite.dev/config/
export default defineConfig((conf: any) => {
  const mode = conf.mode
  const ENV = loadEnv(mode, envDir)
  const proxyConf: Record<string, string | ProxyOptions> = {}
  proxyConf['/admin/api'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/admin/api-doc'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/chat/api'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/chat/api-doc'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
  }
  proxyConf['/doc'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/schema'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/static'] = {
    target: 'http://127.0.0.1:8080',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }

  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}.+\/oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/get_url\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  return {
    preflight: false,
    lintOnSave: false,
    base: './',
    envDir: envDir,
    plugins: [
      vue(),
      vueJsx(),
      DefineOptions(),
      localBasePathFallbackPlugin(ENV.VITE_BASE_PATH, ENV.VITE_ENTRY),
      createHtmlPlugin({ template: ENV.VITE_ENTRY }),
      renameHtmlPlugin(`dist${ENV.VITE_BASE_PATH}`, ENV.VITE_ENTRY),
    ],
    server: {
      cors: true,
      // Bind the IPv6 wildcard so localhost (::1) and IPv4 loopback both work.
      host: '::',
      port: Number(ENV.VITE_APP_PORT),
      strictPort: true,
      proxy: proxyConf,
    },
    build: {
      outDir: `dist${ENV.VITE_BASE_PATH}`,
      target: 'es2022',
      rollupOptions: {
        input: ENV.VITE_ENTRY,
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
