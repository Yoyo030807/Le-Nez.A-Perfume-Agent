<template>
  <section class="sa-atelier-root">
    <!-- 侧边栏：历史配方 -->
    <aside class="sa-atelier-sidebar" :class="{ 'sa-atelier-sidebar--open': sidebarOpen }">
      <div class="sa-atelier-sidebar-header">
        <h3 class="sa-atelier-sidebar-title sa-serif">
          <span v-if="locale === 'zh'">我的香水配方</span>
          <span v-else>My Perfume Recipes</span>
        </h3>
        <button
          class="sa-atelier-sidebar-close"
          type="button"
          @click="sidebarOpen = false"
          aria-label="Close sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M15 5L5 15M5 5l10 10"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
      <div class="sa-atelier-sidebar-content">
        <button
          class="sa-atelier-sidebar-new-btn sa-btn sa-btn--sage"
          type="button"
          @click="startNewRecipe"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 3v10M3 8h10"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
          <span v-if="locale === 'zh'">新建配方</span>
          <span v-else>New Recipe</span>
        </button>
        <div v-if="loadingRecipes" class="sa-atelier-sidebar-loading">
          <span v-if="locale === 'zh'">加载中...</span>
          <span v-else>Loading...</span>
        </div>
        <div v-else-if="recipes.length === 0" class="sa-atelier-sidebar-empty">
          <span v-if="locale === 'zh'">暂无配方</span>
          <span v-else>No recipes yet</span>
        </div>
        <div v-else class="sa-atelier-sidebar-list">
          <button
            v-for="recipe in recipes"
            :key="recipe.id"
            class="sa-atelier-sidebar-item"
            :class="{ 'sa-atelier-sidebar-item--active': selectedRecipeId === recipe.id }"
            type="button"
            @click="selectRecipe(recipe.id)"
          >
            <div class="sa-atelier-sidebar-item-title">{{ recipe.name }}</div>
            <div class="sa-atelier-sidebar-item-desc">{{ recipe.description }}</div>
            <div class="sa-atelier-sidebar-item-time">{{ formatRecipeTime(recipe.created_at) }}</div>
          </button>
        </div>
      </div>
    </aside>

    <!-- 侧边栏遮罩层 -->
    <div
      v-if="sidebarOpen"
      class="sa-atelier-sidebar-overlay"
      @click="sidebarOpen = false"
    ></div>

    <div class="sa-atelier-container">
      <!-- 左侧：配方输入区 -->
      <div ref="formPanelRef" class="sa-atelier-form-panel sa-morandi-card">
        <header class="sa-atelier-header">
          <div class="sa-atelier-header-top">
            <h2 class="sa-atelier-title sa-serif">
              <span v-if="locale === 'zh'">The Atelier</span>
              <span v-else>The Atelier</span>
              <span class="sa-atelier-title-sub">
                <span v-if="locale === 'zh'">｜香水画室</span>
                <span v-else>｜Perfume Atelier</span>
              </span>
            </h2>
            <button
              class="sa-atelier-history-btn"
              type="button"
              @click="sidebarOpen = true"
              aria-label="Open recipe history"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M2 4h16M2 8h16M2 12h12"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>
          <p class="sa-atelier-subtitle">
            <span v-if="locale === 'zh'">将无形的香气凝结为有形的设计</span>
            <span v-else>Condense intangible scents into tangible designs</span>
          </p>
        </header>

        <form class="sa-atelier-form" @submit.prevent="handleGenerate">
          <!-- Import from Journal 按钮 -->
          <div class="sa-atelier-import-section">
            <button
              type="button"
              class="sa-atelier-import-btn"
              @click="showImportModal = true"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M2 4h12M2 8h12M2 12h8"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
              <span v-if="locale === 'zh'">📖 从手札导入</span>
              <span v-else>📖 Import from Journal</span>
            </button>
          </div>

          <div class="sa-atelier-field">
            <label class="sa-atelier-label sa-serif">
              <span v-if="locale === 'zh'">Perfume Name</span>
              <span v-else>Perfume Name</span>
            </label>
            <input
              v-model="recipeName"
              type="text"
              class="sa-atelier-input"
              :placeholder="locale === 'zh' ? '例如：Book of Yesterday' : 'e.g., Book of Yesterday'"
              required
            />
          </div>

          <div class="sa-atelier-field">
            <label class="sa-atelier-label sa-serif">
              <span v-if="locale === 'zh'">Scent Notes</span>
              <span v-else>Scent Notes</span>
            </label>
            <textarea
              v-model="scentKeywords"
              class="sa-atelier-textarea"
              :placeholder="locale === 'zh' ? '例如：潮湿、苔藓、墨水、旧书' : 'e.g., damp, moss, ink, old books'"
              rows="4"
              required
            ></textarea>
            <p class="sa-atelier-hint">
              <span v-if="locale === 'zh'">用关键词描述香调的氛围</span>
              <span v-else>Describe the mood of the scent with keywords</span>
            </p>
          </div>

          <!-- 空状态引导 -->
          <div v-if="!recipeName && !scentKeywords && !extracting" class="sa-atelier-empty-state">
            <p class="sa-atelier-empty-text">
              <span v-if="locale === 'zh'">没有灵感？去和 Le Nez 聊聊</span>
              <span v-else>Lack of inspiration? Chat with Le Nez to find your scent.</span>
            </p>
            <a href="/chat" class="sa-atelier-empty-link sa-btn sa-btn--ghost">
              <span v-if="locale === 'zh'">前往沙龙</span>
              <span v-else>Go to Salon</span>
            </a>
          </div>

          <button
            type="submit"
            class="sa-atelier-submit-btn sa-btn sa-btn--sage"
            :disabled="loading || extracting"
          >
            <span v-if="loading">
              <span v-if="locale === 'zh'">正在凝结香气...</span>
              <span v-else>Condensing Scent...</span>
            </span>
            <span v-else-if="extracting">
              <span v-if="locale === 'zh'">正在提取配方...</span>
              <span v-else>Extracting Recipe...</span>
            </span>
            <span v-else>
              <span v-if="locale === 'zh'">Distill Visuals</span>
              <span v-else>Distill Visuals</span>
            </span>
          </button>
        </form>

        <!-- Import Modal -->
        <div v-if="showImportModal" class="sa-atelier-modal-overlay" @click="showImportModal = false">
          <div class="sa-atelier-modal" @click.stop>
            <div class="sa-atelier-modal-header">
              <h3 class="sa-atelier-modal-title sa-serif">
                <span v-if="locale === 'zh'">从手札导入</span>
                <span v-else>Import from Journal</span>
              </h3>
              <button
                class="sa-atelier-modal-close"
                type="button"
                @click="showImportModal = false"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path
                    d="M15 5L5 15M5 5l10 10"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>
            <div class="sa-atelier-modal-content">
              <div v-if="loadingConversations" class="sa-atelier-modal-loading">
                <span v-if="locale === 'zh'">加载中...</span>
                <span v-else>Loading...</span>
              </div>
              <div v-else-if="conversations.length === 0" class="sa-atelier-modal-empty">
                <span v-if="locale === 'zh'">暂无对话记录</span>
                <span v-else>No conversations yet</span>
              </div>
              <div v-else class="sa-atelier-modal-list">
                <button
                  v-for="conv in conversations"
                  :key="conv.id"
                  class="sa-atelier-modal-item"
                  type="button"
                  @click="handleImportConversation(conv.id)"
                >
                  <div class="sa-atelier-modal-item-title">{{ conv.title }}</div>
                  <div class="sa-atelier-modal-item-time">{{ formatConversationTime(conv.updated_at) }}</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：图片展示区 -->
      <div ref="displayPanelRef" class="sa-atelier-display-panel sa-morandi-card">
        <div class="sa-atelier-frame">
          <div v-if="loading" class="sa-atelier-loading">
            <div class="sa-atelier-loading-spinner"></div>
            <p class="sa-atelier-loading-text sa-serif">
              <span v-if="locale === 'zh'">正在凝结香气...</span>
              <span v-else>Condensing Scent...</span>
            </p>
          </div>

          <div v-else-if="imageUrl" class="sa-atelier-image-container">
            <div class="sa-atelier-image-card">
              <div class="sa-atelier-image-wrapper">
                <img :src="imageUrl" alt="Generated Perfume Bottle" class="sa-atelier-image" />
                <div class="sa-atelier-date-watermark">
                  <span class="sa-atelier-watermark-date">{{ formatDateWatermark() }}</span>
                  <span class="sa-atelier-watermark-signature">Le Nez</span>
                </div>
              </div>
              <div class="sa-atelier-sketch-notes">
                <h3 class="sa-atelier-sketch-notes-title">— COMPOSITION —</h3>
                <div v-if="perfumeNotes" class="sa-atelier-notes-content">
                  <div v-if="perfumeNotes.has_notes" class="sa-atelier-notes-structured">
                    <div class="sa-atelier-note-item">
                      <span class="sa-atelier-note-label">
                        <span v-if="locale === 'zh'">前调：</span>
                        <span v-else>Top Notes:</span>
                      </span>
                      <span class="sa-atelier-note-value">{{ perfumeNotes.top }}</span>
                    </div>
                    <div class="sa-atelier-note-item">
                      <span class="sa-atelier-note-label">
                        <span v-if="locale === 'zh'">中调：</span>
                        <span v-else>Middle Notes:</span>
                      </span>
                      <span class="sa-atelier-note-value">{{ perfumeNotes.middle }}</span>
                    </div>
                    <div class="sa-atelier-note-item">
                      <span class="sa-atelier-note-label">
                        <span v-if="locale === 'zh'">后调：</span>
                        <span v-else>Base Notes:</span>
                      </span>
                      <span class="sa-atelier-note-value">{{ perfumeNotes.base }}</span>
                    </div>
                  </div>
                  <div v-else class="sa-atelier-notes-single">
                    <p class="sa-atelier-note-single-text">
                      <span v-if="locale === 'zh'">单一香调：</span>
                      <span v-else>Single Note:</span>
                      {{ perfumeNotes.single }}
                    </p>
                  </div>
                </div>
                <div v-else class="sa-atelier-notes-loading">
                  <p class="sa-atelier-sketch-notes-text">{{ scentKeywords }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="sa-atelier-placeholder">
            <svg
              width="64"
              height="64"
              viewBox="0 0 64 64"
              fill="none"
              class="sa-atelier-placeholder-icon"
            >
              <path
                d="M32 12L20 20V44L32 52L44 44V20L32 12Z"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M20 20L32 28L44 20"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M32 28V52"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            <p class="sa-atelier-placeholder-text sa-serif">
              <span v-if="locale === 'zh'">等待生成视觉</span>
              <span v-else>Awaiting Visual Generation</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, onUpdated, nextTick } from "vue";
import { API_BASE_URL } from '../../../../config';

type Locale = "zh" | "en";

// 检测用户语言设置（与 PerfumeChat 保持一致）
const detectLocale = (): Locale => {
  if (typeof window !== "undefined") {
    // 检查 localStorage 中是否有保存的语言设置
    const savedLocale = localStorage.getItem("leNez_locale");
    if (savedLocale === "zh" || savedLocale === "en") {
      return savedLocale as Locale;
    }
    // 检查 VitePress 的语言设置
    const htmlLang = document.documentElement.lang || document.documentElement.getAttribute("lang");
    if (htmlLang && htmlLang.startsWith("zh")) {
      return "zh";
    }
    // 检查浏览器语言
    const browserLang = navigator.language || (navigator as any).userLanguage;
    if (browserLang && browserLang.startsWith("zh")) {
      return "zh";
    }
  }
  return "zh"; // 默认中文，与 PerfumeChat 保持一致
};

const locale = ref<Locale>(detectLocale());

// 监听语言变化（如果 PerfumeChat 切换了语言）
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === "leNez_locale" && e.newValue) {
      locale.value = e.newValue as Locale;
    }
  });
}
const recipeName = ref("");
const scentKeywords = ref("");
const imageUrl = ref<string | null>(null);
const loading = ref(false);
const extracting = ref(false);
const perfumeNotes = ref<{
  has_notes: boolean;
  top?: string;
  middle?: string;
  base?: string;
  single?: string;
} | null>(null);
const formPanelRef = ref<HTMLElement | null>(null);
const displayPanelRef = ref<HTMLElement | null>(null);
const showImportModal = ref(false);
const conversations = ref<Array<{ id: string; title: string; updated_at: string }>>([]);
const loadingConversations = ref(false);
const sidebarOpen = ref(false);
const recipes = ref<Array<{ id: string; name: string; description: string; created_at: string }>>([]);
const loadingRecipes = ref(false);
const selectedRecipeId = ref<string | null>(null);

// 同步右侧面板高度与左侧一致
const syncHeights = () => {
  nextTick(() => {
    if (formPanelRef.value && displayPanelRef.value) {
      const formHeight = formPanelRef.value.offsetHeight;
      displayPanelRef.value.style.height = `${formHeight}px`;
    }
  });
};

// 强制应用黑夜模式样式
const forceDarkModeStyles = () => {
  nextTick(() => {
    const isDark = document.documentElement.classList.contains("dark");
    const formPanel = formPanelRef.value;
    
    if (formPanel && isDark) {
      // 强制设置背景色
      (formPanel as HTMLElement).style.setProperty("background", "#4a4a4a", "important");
      
      // 强制设置所有文字颜色为白色（包括所有子元素）
      const allTextElements = formPanel.querySelectorAll(
        "*"
      );
      allTextElements.forEach((el) => {
        const element = el as HTMLElement;
        // 排除按钮和输入框（它们有自己的样式）
        if (!element.matches("button, input, textarea, .sa-atelier-submit-btn")) {
          const computedStyle = window.getComputedStyle(element);
          // 只设置原本是深色的文字
          if (computedStyle.color && 
              (computedStyle.color.includes("rgb(63, 60, 55)") || 
               computedStyle.color.includes("rgb(130, 126, 118)") ||
               computedStyle.color.includes("#3f3c37") ||
               computedStyle.color.includes("#827e76"))) {
            element.style.setProperty("color", "#f5f1ea", "important");
          }
        }
      });
      
      // 强制设置标题、标签等特定元素
      const specificElements = formPanel.querySelectorAll(
        ".sa-atelier-title, .sa-atelier-title-sub, .sa-atelier-subtitle, .sa-atelier-label, .sa-atelier-hint, h2, p"
      );
      specificElements.forEach((el) => {
        (el as HTMLElement).style.setProperty("color", "#f5f1ea", "important");
      });
      
      // 强制设置输入框样式
      const inputs = formPanel.querySelectorAll("input, textarea");
      inputs.forEach((el) => {
        const input = el as HTMLInputElement | HTMLTextAreaElement;
        input.style.setProperty("background", "transparent", "important");
        input.style.setProperty("color", "#f5f1ea", "important");
        input.style.setProperty("border-color", "rgba(255, 255, 255, 0.1)", "important");
      });
      
      // 强制设置占位符文字颜色（使用多个方法确保生效）
      // 方法1: 动态添加全局样式（最高优先级）
      let styleEl = document.getElementById("atelier-placeholder-style") as HTMLStyleElement;
      if (!styleEl) {
        styleEl = document.createElement("style");
        styleEl.id = "atelier-placeholder-style";
        document.head.appendChild(styleEl);
      }
      
      // 使用最高优先级的选择器，包含所有可能的组合
      styleEl.textContent = `
        html.dark .sa-atelier-form-panel input::placeholder,
        html.dark .sa-atelier-form-panel textarea::placeholder,
        html.dark .sa-atelier-form-panel input::-webkit-input-placeholder,
        html.dark .sa-atelier-form-panel textarea::-webkit-input-placeholder,
        html.dark .sa-atelier-form-panel input::-moz-placeholder,
        html.dark .sa-atelier-form-panel textarea::-moz-placeholder,
        html.dark .sa-atelier-form-panel input:-ms-input-placeholder,
        html.dark .sa-atelier-form-panel textarea:-ms-input-placeholder,
        html.dark .sa-atelier-input::placeholder,
        html.dark .sa-atelier-textarea::placeholder,
        html.dark .sa-atelier-input::-webkit-input-placeholder,
        html.dark .sa-atelier-textarea::-webkit-input-placeholder,
        html.dark .sa-atelier-input::-moz-placeholder,
        html.dark .sa-atelier-textarea::-moz-placeholder,
        html.dark .sa-atelier-input:-ms-input-placeholder,
        html.dark .sa-atelier-textarea:-ms-input-placeholder,
        .dark .sa-atelier-form-panel input::placeholder,
        .dark .sa-atelier-form-panel textarea::placeholder,
        .dark .sa-atelier-form-panel input::-webkit-input-placeholder,
        .dark .sa-atelier-form-panel textarea::-webkit-input-placeholder,
        .dark .sa-atelier-form-panel input::-moz-placeholder,
        .dark .sa-atelier-form-panel textarea::-moz-placeholder,
        .dark .sa-atelier-form-panel input:-ms-input-placeholder,
        .dark .sa-atelier-form-panel textarea:-ms-input-placeholder,
        html.dark input[data-dark-placeholder]::placeholder,
        html.dark textarea[data-dark-placeholder]::placeholder,
        html.dark input[data-dark-placeholder]::-webkit-input-placeholder,
        html.dark textarea[data-dark-placeholder]::-webkit-input-placeholder,
        html.dark input[data-dark-placeholder]::-moz-placeholder,
        html.dark textarea[data-dark-placeholder]::-moz-placeholder,
        html.dark input[data-dark-placeholder]:-ms-input-placeholder,
        html.dark textarea[data-dark-placeholder]:-ms-input-placeholder {
          color: #f5f1ea !important;
          opacity: 1 !important;
          -webkit-text-fill-color: #f5f1ea !important;
        }
      `;
      
      // 为每个输入框添加data属性
      inputs.forEach((el) => {
        const input = el as HTMLInputElement | HTMLTextAreaElement;
        input.setAttribute("data-dark-placeholder", "true");
      });
    } else if (formPanel && !isDark) {
      // 白天模式：清除内联样式
      (formPanel as HTMLElement).style.removeProperty("background");
      const allTextElements = formPanel.querySelectorAll("*");
      allTextElements.forEach((el) => {
        (el as HTMLElement).style.removeProperty("color");
      });
      const inputs = formPanel.querySelectorAll("input, textarea");
      inputs.forEach((el) => {
        const input = el as HTMLInputElement | HTMLTextAreaElement;
        input.style.removeProperty("background");
        input.style.removeProperty("color");
        input.style.removeProperty("border-color");
      });
    }
  });
};

// 提取配方信息
const extractRecipe = async (text: string) => {
  extracting.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/api/extract_recipe`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, locale: locale.value }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data.name) recipeName.value = data.name;
    if (data.keywords) scentKeywords.value = data.keywords;
    
    // 重新加载配方列表
    await loadRecipes();
  } catch (error) {
    console.error("提取配方失败:", error);
    alert(
      locale.value === "zh"
        ? `提取失败: ${error instanceof Error ? error.message : "未知错误"}`
        : `Extraction failed: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  } finally {
    extracting.value = false;
  }
};

// 加载对话列表
const loadConversations = async () => {
  loadingConversations.value = true;
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/conversations?locale=${locale.value}`
    );
    if (!response.ok) return;
    const data = await response.json();
    conversations.value = data;
  } catch (error) {
    console.error("加载对话列表失败:", error);
  } finally {
    loadingConversations.value = false;
  }
};

// 从对话导入
const handleImportConversation = async (conversationId: string) => {
  showImportModal.value = false;
  extracting.value = true;
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/conversations/${encodeURIComponent(conversationId)}?locale=${locale.value}`
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    const messages = data.messages || [];
    // 合并所有消息内容
    const fullText = messages.map((m: { content: string }) => m.content).join("\n\n");
    
    // 提取配方
    await extractRecipe(fullText);
  } catch (error) {
    console.error("导入对话失败:", error);
    alert(
      locale.value === "zh"
        ? `导入失败: ${error instanceof Error ? error.message : "未知错误"}`
        : `Import failed: ${error instanceof Error ? error.message : "Unknown error"}`
    );
    extracting.value = false;
  }
};

// 格式化对话时间
const formatConversationTime = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } else if (diffDays === 1) {
    return locale.value === "zh" ? "昨天" : "Yesterday";
  } else if (diffDays < 7) {
    return `${diffDays}${locale.value === "zh" ? "天前" : " days ago"}`;
  } else {
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  }
};

// 格式化配方时间
const formatRecipeTime = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
  } else if (diffDays === 1) {
    return locale.value === "zh" ? "昨天" : "Yesterday";
  } else if (diffDays < 7) {
    return `${diffDays}${locale.value === "zh" ? "天前" : " days ago"}`;
  } else {
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  }
};

// 格式化日期水印 (YYYY.MM.DD)
const formatDateWatermark = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}.${month}.${day}`;
};

// 加载配方列表
const loadRecipes = async () => {
  loadingRecipes.value = true;
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/recipes?locale=${locale.value}`
    );
    if (!response.ok) return;
    const data = await response.json();
    recipes.value = data;
  } catch (error) {
    console.error("加载配方列表失败:", error);
  } finally {
    loadingRecipes.value = false;
  }
};

// 新建配方
const startNewRecipe = () => {
  recipeName.value = "";
  scentKeywords.value = "";
  imageUrl.value = null;
  perfumeNotes.value = null;
  selectedRecipeId.value = null;
  sidebarOpen.value = false;
};

// 选择配方
const selectRecipe = async (recipeId: string) => {
  selectedRecipeId.value = recipeId;
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/recipes/${encodeURIComponent(recipeId)}`
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    recipeName.value = data.name || "";
    scentKeywords.value = data.keywords || "";
    imageUrl.value = data.image_url || null;
    perfumeNotes.value = data.notes || null;
    sidebarOpen.value = false;
  } catch (error) {
    console.error("加载配方详情失败:", error);
    alert(
      locale.value === "zh"
        ? `加载失败: ${error instanceof Error ? error.message : "未知错误"}`
        : `Load failed: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
};

// 从 URL 参数获取数据（如果从 Chat 页面跳转过来）
onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const name = params.get("name");
  const notes = params.get("notes");
  const extractFrom = params.get("extract_from");
  
  // 优先使用 extract_from 参数
  if (extractFrom) {
    const decodedText = decodeURIComponent(extractFrom);
    await extractRecipe(decodedText);
  } else if (name) {
    recipeName.value = name;
  }
  if (notes) {
    scentKeywords.value = notes;
  }
  
  // 加载对话列表（用于导入功能）
  await loadConversations();
  
  // 加载配方列表
  await loadRecipes();
  
  // 同步高度
  syncHeights();
  
  // 强制应用黑夜模式样式
  forceDarkModeStyles();
  
  // 监听窗口大小变化
  window.addEventListener('resize', syncHeights);
  
  // 使用 ResizeObserver 监听左侧面板高度变化
  if (formPanelRef.value) {
    const resizeObserver = new ResizeObserver(() => {
      syncHeights();
    });
    resizeObserver.observe(formPanelRef.value);
  }
  
  // 监听主题切换
  const styleObserver = new MutationObserver(() => {
    forceDarkModeStyles();
  });
  
  styleObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
});

onUpdated(() => {
  syncHeights();
  forceDarkModeStyles();
});

const handleGenerate = async () => {
  if (!recipeName.value.trim() || !scentKeywords.value.trim()) {
    return;
  }

  loading.value = true;
  imageUrl.value = null;
  perfumeNotes.value = null;

  try {
    const response = await fetch(`${API_BASE_URL}/api/draw_bottle`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        recipe_name: recipeName.value.trim(),
        scent_keywords: scentKeywords.value.trim(),
        locale: locale.value,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    imageUrl.value = data.image_url;
    
    // 保存前中后调信息
    if (data.notes) {
      perfumeNotes.value = data.notes;
    } else {
      perfumeNotes.value = null;
    }
    
    // 重新加载配方列表
    await loadRecipes();
  } catch (error) {
    console.error("生成图片失败:", error);
    alert(
      locale.value === "zh"
        ? `生成失败: ${error instanceof Error ? error.message : "未知错误"}`
        : `Generation failed: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.sa-atelier-root {
  position: relative;
  width: 100%;
  min-height: calc(100vh - 4rem);
  padding: 2rem 0;
  overflow-x: visible;
}

.sa-atelier-container {
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  gap: 70px;
  width: 100%;
  margin: 0 auto;
  padding: 0;
  transition: all 0.3s ease-out;
}

/* 左侧表单面板 - 手札大小 */
.sa-atelier-form-panel {
  flex: 0 0 450px;
  max-width: 450px;
  width: 450px;
  min-width: 450px;
  padding: 2rem 2.2rem 1.8rem;
  position: sticky;
  top: 2rem;
  align-self: flex-start;
  margin-left: 70px;
  margin-right: 0;
  background: linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.9),
      rgba(245, 242, 236, 0.92)
    ),
    repeating-linear-gradient(
      to bottom,
      rgba(214, 207, 194, 0.3),
      rgba(214, 207, 194, 0.3) 1px,
      transparent 1px,
      transparent 26px
    );
  border-radius: 14px;
  border: 1px solid rgba(196, 186, 172, 0.5);
  transition: all 0.3s ease-out;
  height: fit-content;
  max-height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.sa-atelier-form-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at top right,
    rgba(196, 154, 156, 0.15) 0,
    transparent 60%
  );
  mix-blend-mode: soft-light;
  pointer-events: none;
  border-radius: 14px;
}

/* 右侧图片展示区 - 聊天框大小 */
.sa-atelier-display-panel {
  flex: 0 0 33.33vw;
  max-width: 33.33vw;
  width: 33.33vw;
  min-width: 33.33vw;
  padding: 2rem 2.2rem 2rem;
  margin-left: 0;
  margin-right: 70px;
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  overflow: visible;
  box-sizing: border-box;
  position: relative;
}

.sa-atelier-header {
  margin-bottom: 1.4rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px dashed rgba(196, 186, 172, 0.5);
  position: relative;
  z-index: 1;
}

.sa-atelier-title {
  font-size: 1.8rem;
  font-weight: 400;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0 0 0.5rem 0;
}

.sa-atelier-title-sub {
  font-size: 0.95rem;
  color: var(--sa-muted);
  font-weight: normal;
  text-transform: none;
  letter-spacing: 0.05em;
}

.sa-atelier-subtitle {
  font-size: 0.95rem;
  color: var(--sa-muted);
  line-height: 1.6;
  margin: 0;
}

.sa-atelier-form {
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.sa-atelier-field {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.sa-atelier-label {
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--sa-ink);
  font-weight: 500;
}

.sa-atelier-input,
.sa-atelier-textarea {
  width: 100%;
  padding: 0.9rem 1.2rem;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--sa-border);
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: var(--sa-font-sans);
  color: var(--sa-ink);
  transition: all 0.2s ease;
}

.sa-atelier-input:focus,
.sa-atelier-textarea:focus {
  outline: none;
  border-color: var(--sa-sage);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 0 0 3px rgba(163, 177, 138, 0.1);
}

.sa-atelier-textarea {
  resize: vertical;
  min-height: 100px;
  line-height: 1.6;
}

.sa-atelier-hint {
  font-size: 0.8rem;
  color: var(--sa-muted);
  margin: 0;
}

.sa-atelier-submit-btn {
  margin-top: 0.5rem;
  width: 100%;
  justify-content: center;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sa-atelier-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Import Section */
.sa-atelier-import-section {
  margin-bottom: 1rem;
}

.sa-atelier-import-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--sa-border);
  border-radius: 8px;
  color: var(--sa-muted);
  font-size: 0.8rem;
  font-family: var(--sa-font-serif);
  letter-spacing: 0.06em;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sa-atelier-import-btn:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: var(--sa-sage);
  color: var(--sa-sage);
}

.sa-atelier-import-btn svg {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

/* Empty State */
.sa-atelier-empty-state {
  margin: 1.5rem 0;
  padding: 1.5rem;
  text-align: center;
  background: rgba(163, 177, 138, 0.05);
  border-radius: 12px;
  border: 1px dashed var(--sa-border);
}

.sa-atelier-empty-text {
  font-size: 0.85rem;
  color: var(--sa-muted);
  margin: 0 0 1rem 0;
  font-style: italic;
}

.sa-atelier-empty-link {
  text-decoration: none;
  display: inline-block;
}

/* Modal */
.sa-atelier-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.sa-atelier-modal {
  background: var(--sa-card-glass);
  backdrop-filter: blur(18px);
  border: 1px solid var(--sa-border);
  border-radius: 20px;
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--sa-shadow-soft);
}

.sa-atelier-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--sa-border);
}

.sa-atelier-modal-title {
  font-size: 1.2rem;
  font-weight: 400;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
}

.sa-atelier-modal-close {
  background: transparent;
  border: none;
  color: var(--sa-muted);
  cursor: pointer;
  padding: 0.3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.sa-atelier-modal-close:hover {
  color: var(--sa-ink);
}

.sa-atelier-modal-content {
  padding: 1.5rem 2rem;
  overflow-y: auto;
  flex: 1;
  max-height: 60vh;
  min-height: 200px;
}

.sa-atelier-modal-content::-webkit-scrollbar {
  width: 8px;
}

.sa-atelier-modal-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.sa-atelier-modal-content::-webkit-scrollbar-thumb {
  background: var(--sa-border);
  border-radius: 4px;
}

.sa-atelier-modal-content::-webkit-scrollbar-thumb:hover {
  background: var(--sa-sage);
}

.sa-atelier-modal-loading,
.sa-atelier-modal-empty {
  text-align: center;
  color: var(--sa-muted);
  padding: 2rem;
  font-size: 0.9rem;
}

.sa-atelier-modal-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sa-atelier-modal-item {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid var(--sa-border);
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sa-atelier-modal-item:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: var(--sa-sage);
}

.sa-atelier-modal-item-title {
  font-size: 0.9rem;
  color: var(--sa-ink);
  margin-bottom: 0.3rem;
  line-height: 1.4;
}

.sa-atelier-modal-item-time {
  font-size: 0.75rem;
  color: var(--sa-muted);
}

.sa-atelier-frame {
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(196, 186, 172, 0.8);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  z-index: 1;
  flex: 1;
}

.sa-atelier-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  color: var(--sa-muted);
}

.sa-atelier-loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--sa-border);
  border-top-color: var(--sa-sage);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.sa-atelier-loading-text {
  font-size: 0.9rem;
  letter-spacing: 0.08em;
  color: var(--sa-muted);
}

.sa-atelier-image-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.sa-atelier-image-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.sa-atelier-image-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sa-atelier-image {
  width: 100%;
  height: auto;
  max-height: 70%;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(30, 30, 28, 0.2);
}

.sa-atelier-date-watermark {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  font-family: var(--sa-font-serif), serif;
  font-size: 0.7rem;
  color: rgba(130, 126, 118, 0.6);
  pointer-events: none;
  user-select: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.2rem;
  line-height: 1.2;
}

.sa-atelier-watermark-date {
  font-style: italic;
}

.sa-atelier-watermark-signature {
  font-weight: 500;
  letter-spacing: 0.1em;
  font-style: normal;
}

.sa-atelier-sketch-notes {
  width: 100%;
  max-width: 90%;
  text-align: center;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.4);
  border: 1px dashed rgba(196, 186, 172, 0.5);
  border-radius: 8px;
}

.sa-atelier-sketch-notes-title {
  font-family: var(--sa-font-serif), serif;
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  color: var(--sa-muted);
  margin: 0 0 0.8rem 0;
  font-weight: 400;
  text-transform: uppercase;
}

.sa-atelier-sketch-notes-text {
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  color: rgba(63, 60, 55, 0.8);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.sa-atelier-image-caption {
  margin-top: 1rem;
  font-size: 0.75rem;
  color: var(--sa-muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-family: var(--sa-font-serif);
}

.sa-atelier-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--sa-muted);
  padding: 2rem;
}

.sa-atelier-placeholder-icon {
  opacity: 0.4;
}

.sa-atelier-placeholder-text {
  font-size: 0.9rem;
  letter-spacing: 0.08em;
  color: var(--sa-muted);
}

/* Dark Mode */
:global(.dark) .sa-atelier-form-panel {
  background: #4a4a4a !important; /* 深灰色背景，与手札面板一致 */
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-form-panel *,
:global(.dark) .sa-atelier-header,
:global(.dark) .sa-atelier-title,
:global(.dark) .sa-atelier-title-sub,
:global(.dark) .sa-atelier-subtitle,
:global(.dark) .sa-atelier-label,
:global(.dark) .sa-atelier-hint {
  color: #f5f1ea !important; /* 白色文字，与手札文字一致 */
}

:global(.dark) .sa-atelier-input,
:global(.dark) .sa-atelier-textarea {
  background: transparent !important; /* 输入框背景透明，使用容器的深灰色 */
  border-color: var(--sa-border);
  color: #f5f1ea !important; /* 白色文字，在深灰色背景上清晰可见 */
}

:global(.dark) .sa-atelier-input:focus,
:global(.dark) .sa-atelier-textarea:focus {
  background: transparent !important;
  border-color: rgba(163, 177, 138, 0.6);
  color: #f5f1ea !important; /* 聚焦时也保持白色 */
}

/* 占位符文字样式 - 使用全局选择器确保生效，纯白色 */
html.dark .sa-atelier-form-panel input::placeholder,
html.dark .sa-atelier-form-panel textarea::placeholder,
html.dark .sa-atelier-form-panel input::-webkit-input-placeholder,
html.dark .sa-atelier-form-panel textarea::-webkit-input-placeholder,
html.dark .sa-atelier-form-panel input::-moz-placeholder,
html.dark .sa-atelier-form-panel textarea::-moz-placeholder,
html.dark .sa-atelier-form-panel input:-ms-input-placeholder,
html.dark .sa-atelier-form-panel textarea:-ms-input-placeholder,
html.dark .sa-atelier-input::placeholder,
html.dark .sa-atelier-textarea::placeholder,
html.dark .sa-atelier-input::-webkit-input-placeholder,
html.dark .sa-atelier-textarea::-webkit-input-placeholder,
html.dark .sa-atelier-input::-moz-placeholder,
html.dark .sa-atelier-textarea::-moz-placeholder,
html.dark .sa-atelier-input:-ms-input-placeholder,
html.dark .sa-atelier-textarea:-ms-input-placeholder,
.dark .sa-atelier-form-panel input::placeholder,
.dark .sa-atelier-form-panel textarea::placeholder,
.dark .sa-atelier-form-panel input::-webkit-input-placeholder,
.dark .sa-atelier-form-panel textarea::-webkit-input-placeholder,
.dark .sa-atelier-form-panel input::-moz-placeholder,
.dark .sa-atelier-form-panel textarea::-moz-placeholder,
.dark .sa-atelier-form-panel input:-ms-input-placeholder,
.dark .sa-atelier-form-panel textarea:-ms-input-placeholder,
html.dark input[data-dark-placeholder]::placeholder,
html.dark textarea[data-dark-placeholder]::placeholder,
html.dark input[data-dark-placeholder]::-webkit-input-placeholder,
html.dark textarea[data-dark-placeholder]::-webkit-input-placeholder,
html.dark input[data-dark-placeholder]::-moz-placeholder,
html.dark textarea[data-dark-placeholder]::-moz-placeholder,
html.dark input[data-dark-placeholder]:-ms-input-placeholder,
html.dark textarea[data-dark-placeholder]:-ms-input-placeholder {
  color: #f5f1ea !important;
  opacity: 1 !important;
  -webkit-text-fill-color: #f5f1ea !important;
}

:global(.dark) .sa-atelier-display-panel {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-frame {
  background: rgba(30, 30, 28, 0.3);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-loading-text,
:global(.dark) .sa-atelier-placeholder-text,
:global(.dark) .sa-atelier-image-caption {
  color: #f5f1ea !important; /* 白色文字 */
}

:global(.dark) .sa-atelier-date-watermark,
:global(.dark) .sa-atelier-watermark-date,
:global(.dark) .sa-atelier-watermark-signature {
  color: rgba(245, 241, 234, 0.5) !important;
}

:global(.dark) .sa-atelier-sketch-notes {
  background: rgba(30, 30, 28, 0.4);
  border-color: rgba(196, 186, 172, 0.3);
}

:global(.dark) .sa-atelier-sketch-notes-title {
  color: rgba(245, 241, 234, 0.7) !important;
}

:global(.dark) .sa-atelier-sketch-notes-text {
  color: rgba(245, 241, 234, 0.8) !important;
}

:global(.dark) .sa-atelier-note-label {
  color: rgba(245, 241, 234, 0.9) !important;
}

:global(.dark) .sa-atelier-note-value {
  color: rgba(245, 241, 234, 0.7) !important;
}

:global(.dark) .sa-atelier-notes-single,
:global(.dark) .sa-atelier-note-single-text {
  color: rgba(245, 241, 234, 0.7) !important;
}

:global(.dark) .sa-atelier-notes-loading {
  color: rgba(245, 241, 234, 0.8) !important;
}

:global(.dark) .sa-atelier-date-watermark {
  color: rgba(245, 241, 234, 0.5) !important;
}

:global(.dark) .sa-atelier-sketch-notes {
  background: rgba(30, 30, 28, 0.4);
  border-color: rgba(196, 186, 172, 0.3);
}

:global(.dark) .sa-atelier-sketch-notes-title {
  color: rgba(245, 241, 234, 0.7) !important;
}

:global(.dark) .sa-atelier-sketch-notes-text {
  color: rgba(245, 241, 234, 0.8) !important;
}

/* Dark Mode for Modal */
:global(.dark) .sa-atelier-modal {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-modal-title,
:global(.dark) .sa-atelier-modal-item-title {
  color: #f5f1ea !important;
}

:global(.dark) .sa-atelier-modal-item {
  background: rgba(30, 30, 28, 0.5);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-modal-item:hover {
  background: rgba(163, 177, 138, 0.2);
  border-color: rgba(163, 177, 138, 0.4);
}

:global(.dark) .sa-atelier-empty-state {
  background: rgba(163, 177, 138, 0.1);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-empty-text {
  color: #f5f1ea !important;
}

/* 侧边栏样式 */
.sa-atelier-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: var(--sa-card-glass);
  backdrop-filter: blur(18px);
  border-right: 1px solid var(--sa-border);
  box-shadow: var(--sa-shadow-soft);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.sa-atelier-sidebar--open {
  transform: translateX(0);
}

.sa-atelier-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(2px);
  z-index: 999;
}

.sa-atelier-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.2rem 1.4rem;
  border-bottom: 1px solid var(--sa-border);
}

.sa-atelier-sidebar-title {
  font-size: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
  font-weight: 400;
}

.sa-atelier-sidebar-close {
  background: transparent;
  border: none;
  color: var(--sa-muted);
  cursor: pointer;
  padding: 0.3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.sa-atelier-sidebar-close:hover {
  color: var(--sa-ink);
}

.sa-atelier-sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sa-atelier-sidebar-new-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
}

.sa-atelier-sidebar-loading,
.sa-atelier-sidebar-empty {
  text-align: center;
  color: var(--sa-muted);
  padding: 2rem;
  font-size: 0.9rem;
}

.sa-atelier-sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sa-atelier-sidebar-item {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.8rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.sa-atelier-sidebar-item:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: rgba(163, 177, 138, 0.3);
}

.sa-atelier-sidebar-item--active {
  background: rgba(163, 177, 138, 0.15);
  border-color: rgba(163, 177, 138, 0.4);
}

.sa-atelier-sidebar-item-title {
  font-size: 0.9rem;
  color: var(--sa-ink);
  line-height: 1.4;
  font-weight: 500;
}

.sa-atelier-sidebar-item-desc {
  font-size: 0.8rem;
  color: var(--sa-muted);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.sa-atelier-sidebar-item-time {
  font-size: 0.72rem;
  color: var(--sa-muted);
}

.sa-atelier-header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.sa-atelier-history-btn {
  background: transparent;
  border: 1px solid var(--sa-border);
  border-radius: 8px;
  padding: 0.5rem;
  color: var(--sa-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sa-atelier-history-btn:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: var(--sa-sage);
  color: var(--sa-sage);
}

/* 侧边栏黑夜模式 */
:global(.dark) .sa-atelier-sidebar {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

:global(.dark) .sa-atelier-sidebar-overlay {
  background: rgba(0, 0, 0, 0.5);
}

:global(.dark) .sa-atelier-sidebar-item-title {
  color: #f5f1ea !important;
}

:global(.dark) .sa-atelier-sidebar-item-desc {
  color: rgba(245, 241, 234, 0.8) !important;
}

/* Responsive */
@media (max-width: 1024px) {
  .sa-atelier-container {
    flex-direction: column;
    padding: 0 1.5rem;
  }

  .sa-atelier-form-panel {
    flex: 0 0 auto !important;
    width: 100% !important;
    max-width: 100% !important;
    position: relative;
    top: 0;
    max-height: calc(100vh - 4rem);
    margin-top: 0;
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .sa-atelier-display-panel {
    max-width: 100% !important;
    width: 100% !important;
    flex: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
}

@media (max-width: 768px) {
  .sa-atelier-root {
    padding: 1.5rem 0;
  }

  .sa-atelier-container {
    padding: 0 1rem;
    gap: 1.5rem;
  }

  .sa-atelier-form-panel,
  .sa-atelier-display-panel {
    padding: 1.6rem 1.4rem 1.4rem;
  }

  .sa-atelier-frame {
    min-height: 300px;
  }
}
</style>

