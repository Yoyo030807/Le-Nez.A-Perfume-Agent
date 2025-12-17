import DefaultTheme from "vitepress/theme";
import Layout from "./Layout.vue";
import "./styles.css";
import PerfumeChat from "./components/PerfumeChat.vue";
import Atelier from "./components/Atelier.vue";
import LandingPage from "./components/LandingPage.vue";
import Lab from "./components/Lab.vue";

export default {
  ...DefaultTheme,
  Layout,
  enhanceApp({ app, router }) {
    app.component("PerfumeChat", PerfumeChat);
    app.component("Atelier", Atelier);
    app.component("LandingPage", LandingPage);
    app.component("Lab", Lab);
    
    // 控制台彩蛋 - 只在客户端执行
    if (typeof window !== "undefined") {
      // 页面加载时显示
      const showEasterEgg = () => {
        console.log(
          `%c
╔═══════════════════════════════════════╗
║                                       ║
║         SCENT ALCHEMIST               ║
║                                       ║
╚═══════════════════════════════════════╝
          `,
          "color: #a3b18a; font-family: monospace; font-size: 12px;"
        );
        console.log(
          "%cDeveloped by Yaoyao YU. Welcome to the lab. 🧪",
          "color: #a3b18a; font-family: monospace; font-size: 11px; font-weight: bold;"
        );
      };
      
      // 延迟显示，确保 DOM 已加载
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", showEasterEgg);
      } else {
        setTimeout(showEasterEgg, 100);
      }
    }
  },
};



