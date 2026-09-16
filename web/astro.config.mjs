// @ts-check
import { defineConfig, passthroughImageService } from 'astro/config';

// 文章博士 フロントエンド。
// 静的サイトとしてビルドし、Dockerfile が dist/ を Apache の DocumentRoot に
// 配置する。校正 API（/njc.cgi?format=json）は同一オリジンの Perl CGI。
export default defineConfig({
  site: 'https://monjo.no32.tk',
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
  compressHTML: true,
  // 画像最適化（sharp）は使わない。ネイティブ依存を避けてビルドを軽くする。
  image: { service: passthroughImageService() },
  vite: {
    server: {
      // `npm run dev` 中は校正 API を稼働中のコンテナ（or 本番）へ中継する。
      //   例) docker run -p 8080:8080 monjo-hakase && MONJO_API_ORIGIN=http://localhost:8080 npm run dev
      proxy: {
        '/njc.cgi': {
          target: process.env.MONJO_API_ORIGIN ?? 'http://localhost:8080',
          changeOrigin: true,
        },
      },
    },
  },
});
