import { defineConfig } from "vitepress";
import path from "node:path";

export default defineConfig({
  lang: "zh-CN",
  title: "Scent Alchemist | 气味炼金术士",
  description: "A minimalist, high-end scent & tech journal. 极简高端的气味与技术手记。",
  lastUpdated: true,
  themeConfig: {
    logo: "/favicon.svg",
    nav: [
      { text: "Home · 首页", link: "/" },
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/Yoyo030807/Le-Nez.A-Perfume-Agent" },
    ],
  },
  vite: {
    resolve: {
      alias: {
        "@theme": path.resolve(__dirname, "theme"),
        "@": path.resolve(__dirname, "../../../.."),
      },
    },
    server: {
      port: 5174,
      host: true,
    },
  },
});

