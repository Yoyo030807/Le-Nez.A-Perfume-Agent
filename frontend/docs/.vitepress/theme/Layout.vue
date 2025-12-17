<script setup lang="ts">
import DefaultTheme from "vitepress/theme";
import { onMounted } from "vue";

const { Layout: DefaultLayout } = DefaultTheme;

// 在客户端挂载时添加页脚
onMounted(() => {
  if (typeof document !== "undefined") {
    // 检查是否已经存在页脚
    let footer = document.querySelector(".sa-global-footer");
    if (!footer) {
      footer = document.createElement("footer");
      footer.className = "sa-global-footer";
      footer.textContent = "Designed & Coded with ❤️ by Yaoyao YU © 2025";
      
      // 找到 VitePress 的内容容器
      const content = document.querySelector(".VPContent") || document.querySelector("main") || document.body;
      if (content) {
        content.appendChild(footer);
      }
    }
  }
});
</script>

<template>
  <DefaultLayout />
</template>

<style>
.sa-global-footer {
  width: 100%;
  text-align: center;
  padding: 20px 0;
  font-size: 0.8rem;
  color: #aaa;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  background: transparent;
  margin-top: 4rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}
</style>

