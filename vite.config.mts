import {defineConfig} from 'vite';
import {resolve} from 'path';
import viteHtmlResolveAliasPlugin from 'vite-plugin-html-resolve-alias';
import customJinjaPlugin from './build/vite-plugin-custom-jinja';

const ASSET_URL = process.env.ASSET_URL || '/';
const VITE_PORT = process.env.VITE_PORT || 5173;
const VITE_HOST = process.env.VITE_HOST || 'localhost';

const entryPoints = ['login', 'panel', 'label'];

export default defineConfig({
  root: 'front',
  base: `${ASSET_URL}`,
  publicDir: 'public/',
  server: {
    host: '0.0.0.0',
    port: +`${VITE_PORT}`,
    cors: true,
    hmr: {
      host: `${VITE_HOST}`,
    },
  },
  build: {
    outDir: '../dist',
    assetsDir: 'static',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        ...entryPoints.reduce((acc, item) => {
          acc[item] = resolve(__dirname, `front/pages/${item}/${item}.html.jinja2`);
          return acc;
        }, {}),
      },
      // output: {
      //   entryFileNames: 'assets/js/[name]-[hash].js',
      //   chunkFileNames: 'assets/js/[name]-[hash].js',
      //   assetFileNames: (assetInfo) => {
      //     const extType = (assetInfo.name ?? '').split('.')[-1];
      //   },
      // },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'front'),
    },
  },
  plugins: [viteHtmlResolveAliasPlugin(), customJinjaPlugin()],
});
