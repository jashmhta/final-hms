import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import { compression } from 'vite-plugin-compression2'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  plugins: [
    react(),
    // PWA support with optimized caching
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "favicon.ico"],
      manifest: {
        name: "HMS Enterprise-Grade",
        short_name: "HMS",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#1976d2",
        icons: [
          { src: "/pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "/pwa-512x512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,jpg,jpeg,svg,woff,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/static\.example\.com\/.*$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'static-assets',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
              },
            },
          },
          {
            urlPattern: /^https:\/\/api\.example\.com\/.*$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 24 * 60 * 60, // 24 hours
              },
            },
          },
        ],
      },
    }),
    // Bundle analyzer
    visualizer({
      filename: 'bundle-stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
    // Compression
    compression(),
    // Legacy browser support
    legacy({
      targets: ['defaults', 'not IE 11']
    }),
  ],
  server: {
    port: 3000,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
    // Performance optimizations
    hmr: {
      overlay: false
    },
    watch: {
      usePolling: true,
      interval: 100
    }
  },
  build: {
    // Performance optimizations
    target: 'esnext',
    minify: 'terser',
    sourcemap: false,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Optimized chunk splitting
        manualChunks: (id) => {
          // Core React
          if (id.includes('node_modules/react')) {
            return 'react'
          }
          // MUI components
          if (id.includes('node_modules/@mui')) {
            return 'mui'
          }
          // Radix UI components
          if (id.includes('node_modules/@radix-ui')) {
            return 'radix'
          }
          // Charting library
          if (id.includes('node_modules/recharts')) {
            return 'charts'
          }
          // Form handling
          if (id.includes('node_modules/react-hook-form')) {
            return 'forms'
          }
          // State management
          if (id.includes('node_modules/@tanstack') || id.includes('node_modules/react-query')) {
            return 'state'
          }
          // Router
          if (id.includes('node_modules/react-router')) {
            return 'router'
          }
          // Icons
          if (id.includes('node_modules/lucide-react')) {
            return 'icons'
          }
          // Date utilities
          if (id.includes('node_modules/date-fns')) {
            return 'date'
          }
          // HTTP client
          if (id.includes('node_modules/axios')) {
            return 'http'
          }
          // Large vendor chunks
          if (id.includes('node_modules') && id.length > 100) {
            return 'vendor'
          }
        },
        // Optimized file names
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').slice(-1)[0]
            : 'chunk'
          return `js/${facadeModuleId}-[hash].js`
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash][extname]`
          }
          if (/woff|woff2/.test(ext)) {
            return `fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      },
      // Performance optimizations
      treeshake: true,
      experimentalOptimizeChunkImports: true
    },
    // Terser optimization
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log']
      },
      format: {
        comments: false
      }
    }
  },
  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@tanstack/react-query',
      'react-hook-form',
      'recharts',
      'date-fns',
      'axios'
    ],
    exclude: []
  },
  // CSS optimizations
  css: {
    modules: {
      localsConvention: 'camelCase'
    },
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";`
      }
    }
  },
  // Path aliases
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/components': resolve(__dirname, './src/components'),
      '@/pages': resolve(__dirname, './src/pages'),
      '@/hooks': resolve(__dirname, './src/hooks'),
      '@/utils': resolve(__dirname, './src/utils'),
      '@/styles': resolve(__dirname, './src/styles'),
      '@/types': resolve(__dirname, './src/types'),
      '@/store': resolve(__dirname, './src/store'),
      '@/services': resolve(__dirname, './src/services')
    }
  },
  // Define global constants
  define: {
    __VITE_OPTIONS_API__: true,
    __VITE_PROD__: true,
    'import.meta.env.PROD': true,
  },
  // Worker bundle optimization
  worker: {
    format: 'es',
    plugins: [
      react()
    ],
    rollupOptions: {
      output: {
        chunkFileNames: 'js/workers/[name]-[hash].js',
        entryFileNames: 'js/workers/[name]-[hash].js'
      }
    }
  }
})