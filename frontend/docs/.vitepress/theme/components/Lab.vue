<template>
  <section class="sa-lab-root">
    <!-- 侧边栏按钮 -->
    <button
      class="sa-sidebar-toggle-btn"
      type="button"
      @click="sidebarOpen = true"
      aria-label="Toggle sidebar"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path
          d="M3 5h14M3 10h14M3 15h14"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
    </button>

    <!-- 侧边栏 -->
    <aside class="sa-sidebar" :class="{ 'sa-sidebar--open': sidebarOpen }">
      <div class="sa-sidebar-header">
        <h3 class="sa-sidebar-title sa-serif">
          <span v-if="locale === 'zh'">ARCHIVES</span>
          <span v-else>ARCHIVES</span>
          <span class="sa-sidebar-title-sub">
            <span v-if="locale === 'zh'">｜分析档案</span>
            <span v-else>｜Analysis Archives</span>
          </span>
        </h3>
        <button
          class="sa-sidebar-close"
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
      <div class="sa-sidebar-content">
        <!-- 搜索新香按钮 -->
        <button
          class="sa-sidebar-new-search-btn sa-btn sa-btn--sage"
          type="button"
          @click="handleNewSearch"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 0.5rem;">
            <path
              d="M7.333 12.667A5.333 5.333 0 1 0 7.333 2a5.333 5.333 0 0 0 0 10.667ZM14 14l-2.9-2.9"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span v-if="locale === 'zh'">搜索新香</span>
          <span v-else>New Search</span>
        </button>
        
        <div v-if="searchHistory.length === 0" class="sa-sidebar-empty">
          <span v-if="locale === 'zh'">暂无分析记录</span>
          <span v-else>No analysis records</span>
        </div>
        <div v-else class="sa-sidebar-list">
          <button
            v-for="item in searchHistory"
            :key="item.id"
            class="sa-sidebar-item"
            :class="{ 'sa-sidebar-item--active': selectedHistoryId === item.id }"
            type="button"
            @click="selectHistoryItem(item)"
          >
            <div class="sa-sidebar-item-title">{{ item.perfume_name }}</div>
            <div class="sa-sidebar-item-time">{{ formatHistoryTime(item.timestamp) }}</div>
          </button>
        </div>
      </div>
    </aside>

    <!-- 侧边栏遮罩层 -->
    <div
      v-if="sidebarOpen"
      class="sa-sidebar-overlay"
      @click="sidebarOpen = false"
    ></div>

    <!-- 主内容区域：滚动容器 -->
    <div class="sa-lab-main-scroll-area">
      <!-- 直接放置内容，不包装 -->
      <div class="sa-lab-content-direct" :class="{ 'sa-lab-content-direct--has-data': analysisData && analysisData.found }">
        <!-- Header Section -->
        <div class="sa-lab-header-section">
          <header class="sa-lab-header">
            <h1 class="sa-lab-title sa-serif">
              <span v-if="locale === 'zh'">The Lab</span>
              <span v-else>The Lab</span>
              <span class="sa-lab-title-sub">
                <span v-if="locale === 'zh'">｜成分实验室</span>
                <span v-else>｜Component Laboratory</span>
              </span>
            </h1>
            <p class="sa-lab-subtitle">
              <span v-if="locale === 'zh'">解析香水成分与安全数据</span>
              <span v-else>Analyze perfume components and safety data</span>
            </p>
          </header>

          <!-- Search Form -->
          <form class="sa-lab-search-form" @submit.prevent="handleAnalyze">
            <div class="sa-lab-search-field">
              <input
                v-model="searchQuery"
                type="text"
                class="sa-lab-search-input"
                :placeholder="locale === 'zh' ? '输入香水名称...' : 'Enter perfume name...'"
                required
                :disabled="loading"
              />
              <button
                type="submit"
                class="sa-lab-search-btn sa-btn sa-btn--sage"
                :disabled="loading || !searchQuery.trim()"
              >
                <span v-if="loading">
                  <span v-if="locale === 'zh'">分析中...</span>
                  <span v-else>Analyzing...</span>
                </span>
                <span v-else>
                  <span v-if="locale === 'zh'">分析</span>
                  <span v-else>Analyze</span>
                </span>
              </button>
            </div>
          </form>
        </div>

        <!-- State A: Loading -->
        <div v-if="loading" class="sa-lab-loading">
          <div class="sa-lab-loading-spinner"></div>
          <p class="sa-lab-loading-text">
            <span v-if="locale === 'zh'">正在连接全球香水数据库...</span>
            <span v-else>Connecting to Global Fragrance Database...</span>
          </p>
        </div>

        <!-- State B: Data Found -->
        <div v-else-if="analysisData && analysisData.found" class="sa-lab-analysis-results">
          <div class="sa-lab-results-grid">
            <!-- 1. Radar Chart -->
            <div class="sa-lab-result-card sa-lab-radar-card">
              <h3 class="sa-lab-card-title sa-serif">
                <span v-if="locale === 'zh'">香调雷达图</span>
                <span v-else>Scent Profile</span>
              </h3>
              <div class="sa-lab-chart-container">
                <component
                  v-if="chartData && RadarChart"
                  :is="RadarChart"
                  :data="chartData"
                  :options="chartOptions"
                />
                <div v-else class="sa-lab-chart-placeholder">
                  <span v-if="locale === 'zh'">加载图表中...</span>
                  <span v-else>Loading chart...</span>
                </div>
              </div>
            </div>

            <!-- 2. Overview Card -->
            <div class="sa-lab-result-card sa-lab-overview-card">
              <h3 class="sa-lab-card-title sa-serif">
                <span v-if="locale === 'zh'">总体概括</span>
                <span v-else>Overview</span>
              </h3>
              <div class="sa-lab-card-content">
                <div v-if="analysisData.brand" class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">品牌：</strong>
                  <strong v-else>Brand: </strong>
                  {{ analysisData.brand }}
                </div>
                
                <div class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">名称：</strong>
                  <strong v-else>Name: </strong>
                  {{ analysisData.name }}
                </div>
                
                <div v-if="analysisData.longevity" class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">留香：</strong>
                  <strong v-else>Longevity: </strong>
                  {{ analysisData.longevity }}
                </div>
                
                <div v-if="analysisData.similar_recommendations && analysisData.similar_recommendations.length > 0" class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">相似推荐：</strong>
                  <strong v-else>Similar Recommendations: </strong>
                  <ul class="sa-lab-similar-list">
                    <li v-for="item in analysisData.similar_recommendations" :key="item">{{ item }}</li>
                  </ul>
                </div>
                
                <div v-if="analysisData.reference_urls && analysisData.reference_urls.length > 0" class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">参考信源：</strong>
                  <strong v-else>Reference Sources: </strong>
                  <ul class="sa-lab-reference-list">
                    <li v-for="(url, index) in analysisData.reference_urls" :key="index">
                      <a 
                        :href="url" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        class="sa-lab-reference-link"
                      >
                        {{ getDomainFromUrl(url) }}
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style="margin-left: 0.3rem; display: inline-block; vertical-align: middle;">
                          <path
                            d="M10 2L2 10M2 2h8v8"
                            stroke="currentColor"
                            stroke-width="1.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                          />
                        </svg>
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- 3. Component Data Card -->
            <div class="sa-lab-result-card sa-lab-data-card">
              <h3 class="sa-lab-card-title sa-serif">
                <span v-if="locale === 'zh'">成分数据</span>
                <span v-else>Component Data</span>
              </h3>
              <div class="sa-lab-card-content">
                <div v-if="analysisData.notes && (analysisData.notes.top || analysisData.notes.middle || analysisData.notes.base)" class="sa-lab-notes-section">
                  <div v-if="analysisData.notes.top" class="sa-lab-note-row">
                    <strong v-if="locale === 'zh'">前调：</strong>
                    <strong v-else>Top: </strong>
                    {{ analysisData.notes.top }}
                  </div>
                  <div v-if="analysisData.notes.middle" class="sa-lab-note-row">
                    <strong v-if="locale === 'zh'">中调：</strong>
                    <strong v-else>Middle: </strong>
                    {{ analysisData.notes.middle }}
                  </div>
                  <div v-if="analysisData.notes.base" class="sa-lab-note-row">
                    <strong v-if="locale === 'zh'">后调：</strong>
                    <strong v-else>Base: </strong>
                    {{ analysisData.notes.base }}
                  </div>
                </div>
                
                <div v-if="analysisData.allergens && analysisData.allergens.length > 0" class="sa-lab-info-item sa-lab-info-item--alert">
                  <strong v-if="locale === 'zh'">致敏源：</strong>
                  <strong v-else>Allergens: </strong>
                  {{ analysisData.allergens.join(', ') }}
                </div>
                
                <div v-if="analysisData.safety_brief" class="sa-lab-info-item">
                  <strong v-if="locale === 'zh'">安全评估：</strong>
                  <strong v-else>Safety Assessment: </strong>
                  {{ analysisData.safety_brief }}
                </div>
              </div>
            </div>
          </div>
        
        <div class="sa-lab-source">
          <span v-if="locale === 'zh'">数据来源：Source: Real-time Analysis via Tavily Search.</span>
          <span v-else>Source: Real-time Analysis via Tavily Search.</span>
        </div>
      </div>

      <!-- State C: Not Found -->
      <div v-else-if="analysisData && !analysisData.found" class="sa-lab-not-found">
        <div class="sa-lab-not-found-content">
          <h2 class="sa-lab-not-found-title sa-serif">
            <span v-if="locale === 'zh'">Archive Not Found</span>
            <span v-else>Archive Not Found</span>
          </h2>
          <p class="sa-lab-not-found-text">
            <span v-if="locale === 'zh'">数据库中未收录此香气。也许，这是一款尚未诞生的杰作？</span>
            <span v-else>This fragrance is not found in the database. Perhaps it's a masterpiece yet to be created?</span>
          </p>
          <button
            class="sa-lab-create-btn sa-btn sa-btn--sage"
            type="button"
            @click="handleCreateWithLeNez"
          >
            <span v-if="locale === 'zh'">Create with Le Nez</span>
            <span v-else>Create with Le Nez</span>
          </button>
        </div>
      </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, defineComponent, h, onMounted, shallowRef, markRaw } from "vue";
import { API_BASE_URL } from '../../../../config';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
// 注册 Chart.js 组件
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// 动态导入 vue-chartjs（避免 SSR 问题）
const RadarChart = shallowRef<any>(null);

onMounted(async () => {
  // 加载历史记录
  loadSearchHistory();
  
  try {
    const vueChartJs = await import("vue-chartjs");
    const Radar = vueChartJs.Radar;
    const ChartComponent = defineComponent({
      name: "RadarChart",
      props: {
        data: {
          type: Object,
          required: true,
        },
        options: {
          type: Object,
          default: () => ({}),
        },
      },
      setup(props) {
        return () => h(Radar, { data: props.data as any, options: props.options });
      },
    });
    RadarChart.value = markRaw(ChartComponent);
  } catch (error) {
    console.error("Failed to load vue-chartjs:", error);
    // 占位组件
    const PlaceholderComponent = defineComponent({
      name: "RadarChart",
      props: {
        data: Object,
        options: Object,
      },
      setup() {
        return () => h("div", "Chart unavailable");
      },
    });
    RadarChart.value = markRaw(PlaceholderComponent);
  }
});

type Locale = "zh" | "en";

// 检测用户语言设置
const detectLocale = (): Locale => {
  if (typeof window !== "undefined") {
    const savedLocale = localStorage.getItem("leNez_locale");
    if (savedLocale === "zh" || savedLocale === "en") {
      return savedLocale as Locale;
    }
    const htmlLang = document.documentElement.lang || document.documentElement.getAttribute("lang");
    if (htmlLang && htmlLang.startsWith("zh")) {
      return "zh";
    }
    const browserLang = navigator.language || (navigator as any).userLanguage;
    if (browserLang && browserLang.startsWith("zh")) {
      return "zh";
    }
  }
  return "zh";
};

const locale = ref<Locale>(detectLocale());

// 监听语言变化
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === "leNez_locale" && e.newValue) {
      locale.value = e.newValue as Locale;
    }
  });
}

const searchQuery = ref("");
const loading = ref(false);
const sidebarOpen = ref(false);
const selectedHistoryId = ref<string | null>(null);
const searchHistory = ref<Array<{
  id: string;
  perfume_name: string;
  timestamp: number;
  data?: any;
}>>([]);

const analysisData = ref<{
  found: boolean;
  name?: string;
  brand?: string;
  radar_data?: {
    Floral?: number;
    Woody?: number;
    Fresh?: number;
    Spicy?: number;
    Sweet?: number;
    Oriental?: number;
  };
  notes?: {
    top?: string;
    middle?: string;
    base?: string;
  };
  similar_recommendations?: string[];
  allergens?: string[];
  longevity?: string;
  safety_brief?: string;
  source?: string;
  reference_urls?: string[];
} | null>(null);

// 加载历史记录
const loadSearchHistory = () => {
  if (typeof window === "undefined") return;
  try {
    const stored = localStorage.getItem("lab_search_history");
    if (stored) {
      searchHistory.value = JSON.parse(stored);
      // 按时间倒序排列
      searchHistory.value.sort((a, b) => b.timestamp - a.timestamp);
    }
  } catch (error) {
    console.error("Failed to load search history:", error);
  }
};

// 保存历史记录
const saveToHistory = (perfumeName: string, data: any) => {
  if (typeof window === "undefined") return;
  try {
    const historyItem = {
      id: `lab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      perfume_name: perfumeName,
      timestamp: Date.now(),
      data: data,
    };
    
    // 检查是否已存在相同名称的记录，如果存在则更新
    const existingIndex = searchHistory.value.findIndex(
      (item) => item.perfume_name.toLowerCase() === perfumeName.toLowerCase()
    );
    
    if (existingIndex >= 0) {
      searchHistory.value[existingIndex] = historyItem;
    } else {
      searchHistory.value.unshift(historyItem);
    }
    
    // 限制历史记录数量（最多保留50条）
    if (searchHistory.value.length > 50) {
      searchHistory.value = searchHistory.value.slice(0, 50);
    }
    
    // 保存到 localStorage
    localStorage.setItem("lab_search_history", JSON.stringify(searchHistory.value));
  } catch (error) {
    console.error("Failed to save search history:", error);
  }
};

// 格式化历史记录时间
const getDomainFromUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch {
    // 如果 URL 解析失败，返回原始 URL 的前 30 个字符
    return url.length > 30 ? url.substring(0, 30) + '...' : url;
  }
};

const formatHistoryTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (locale.value === "zh") {
    if (diffMins < 1) return "刚刚";
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  } else {
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
};

// 选择历史记录项
const selectHistoryItem = async (item: any) => {
  selectedHistoryId.value = item.id;
  searchQuery.value = item.perfume_name;
  sidebarOpen.value = false;
  
  // 如果有缓存的数据，直接使用
  if (item.data && item.data.found) {
    analysisData.value = item.data;
  } else {
    // 否则重新调用 API
    await handleAnalyze();
  }
};

// 图表数据
const chartData = computed(() => {
  if (!analysisData.value || !analysisData.value.found || !analysisData.value.radar_data) {
    return null;
  }
  
  const radar = analysisData.value.radar_data;
  const labels = locale.value === "zh" 
    ? ["花香", "木质", "清新", "辛辣", "甜香", "东方"]
    : ["Floral", "Woody", "Fresh", "Spicy", "Sweet", "Oriental"];
  
  return {
    labels: labels,
    datasets: [
      {
        label: locale.value === "zh" ? "香调强度" : "Intensity",
        data: [
          radar.Floral || 0,
          radar.Woody || 0,
          radar.Fresh || 0,
          radar.Spicy || 0,
          radar.Sweet || 0,
          radar.Oriental || 0,
        ],
        backgroundColor: "rgba(163, 177, 138, 0.2)",
        borderColor: "rgba(163, 177, 138, 0.8)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(163, 177, 138, 0.8)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(163, 177, 138, 0.8)",
      },
    ],
  } as any; // 使用类型断言避免 Chart.js 类型检查问题
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: {
      beginAtZero: true,
      max: 10,
      ticks: {
        stepSize: 2,
        font: {
          family: "'Courier New', monospace",
          size: 10,
        },
      },
      pointLabels: {
        font: {
          family: "'Courier New', monospace",
          size: 11,
        },
      },
    },
  },
  plugins: {
    legend: {
      display: false,
    },
  },
};

const handleAnalyze = async () => {
  if (!searchQuery.value.trim() || loading.value) return;
  
  loading.value = true;
  analysisData.value = null;
  selectedHistoryId.value = null;
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze_scent`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: searchQuery.value.trim(),
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    analysisData.value = data;
    
    // 保存到历史记录（仅当找到数据时）
    if (data.found) {
      saveToHistory(searchQuery.value.trim(), data);
    }
  } catch (error) {
    console.error("分析失败:", error);
    alert(
      locale.value === "zh"
        ? `分析失败: ${error instanceof Error ? error.message : "未知错误"}`
        : `Analysis failed: ${error instanceof Error ? error.message : "Unknown error"}`
    );
    analysisData.value = { found: false };
  } finally {
    loading.value = false;
  }
};

const handleNewSearch = () => {
  // 清空当前搜索状态
  searchQuery.value = "";
  analysisData.value = null;
  selectedHistoryId.value = null;
  // 关闭侧边栏
  sidebarOpen.value = false;
  // 可选：聚焦到搜索框（需要给搜索框添加 ref）
};

const handleCreateWithLeNez = () => {
  // 跳转到 /chat，并带上搜索的香水名作为初始话题
  const encodedName = encodeURIComponent(searchQuery.value.trim());
  window.location.href = `/chat?initial_topic=${encodedName}`;
};
</script>

<style scoped>
.sa-lab-root {
  position: relative;
  height: 100vh;
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  padding: 0;
  margin: 0 !important;
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: stretch;
  box-sizing: border-box;
  overflow: hidden;
}

/* 侧边栏按钮（左上角） */
.sa-sidebar-toggle-btn {
  position: fixed;
  top: 5px; /* 几乎贴近顶部 */
  left: 1.5rem;
  z-index: 100;
  background: var(--sa-card-glass);
  border: 1px solid var(--sa-border);
  border-radius: 8px;
  padding: 0.6rem;
  color: var(--sa-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(18px);
  box-shadow: var(--sa-shadow-soft);
}

.sa-sidebar-toggle-btn:hover {
  color: var(--sa-ink);
  background: rgba(163, 177, 138, 0.1);
}

/* 1. 外层滚动容器：必须占满屏幕，滚动条才能在最右边 */
.sa-lab-main-scroll-area {
  flex: 1 1 auto !important; /* 强制占满剩余空间 */
  height: 100vh !important;
  width: 100% !important; /* 使用 100% 而不是 100vw，避免超出屏幕 */
  max-width: 100% !important;
  overflow-y: auto;
  overflow-x: hidden; /* 改为 hidden，防止水平溢出 */
  background: transparent !important;
  box-sizing: border-box;
  position: relative;
  z-index: 1; /* 降低 z-index，确保在 header 和侧边栏下方 */
  margin-top: 0 !important; /* 移除顶部间距，让内容从顶部开始 */
  padding-left: 0; /* 确保不与侧边栏重叠 */
}

/* 2. 直接内容容器：完全铺满，无任何限制 */
.sa-lab-content-direct {
  width: 100% !important; /* 使用 100% 而不是 100vw，避免超出屏幕 */
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  min-height: 100vh; /* 占满整个视口 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center; /* 默认垂直居中 */
  padding-top: 5px !important; /* 几乎贴近顶部 */
  padding-left: 1.5rem !important; /* 左侧间距，避免与侧边栏重叠 */
  padding-right: 1.5rem !important; /* 右侧间距 */
  padding-bottom: 10vh;
  box-sizing: border-box;
  position: relative;
  z-index: 1; /* 降低 z-index */
  transition: justify-content 0.3s ease;
}

/* 有数据时，内容对齐到顶部 */
.sa-lab-content-direct--has-data {
  justify-content: flex-start;
  padding-top: 5px !important; /* 几乎贴近顶部 */
}

/* Header Section */
.sa-lab-header-section {
  width: 100%;
  max-width: 100%; /* 使用 100%，由父容器控制 padding */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem; /* 减少间距，让内容更紧凑 */
  margin-bottom: 1rem; /* 减少底部间距 */
  margin-top: 0; /* 确保没有额外的上边距 */
  padding: 0; /* 移除 padding，由父容器控制 */
  box-sizing: border-box;
}

/* 侧边栏样式 */
.sa-sidebar {
  position: fixed;
  left: 0;
  top: 0; /* 从顶部开始，覆盖整个屏幕 */
  bottom: 0;
  width: 320px;
  background: var(--sa-card-glass);
  backdrop-filter: blur(18px);
  border-right: 1px solid var(--sa-border);
  box-shadow: var(--sa-shadow-soft);
  transform: translateX(-100%);
  transition: transform 0.3s ease-out;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.sa-sidebar--open {
  transform: translateX(0);
}

.sa-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  backdrop-filter: blur(2px);
}

.sa-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(64px + 1.2rem) 1.4rem 1.2rem 1.4rem; /* 顶部 padding 加上 header 高度，避免与 VitePress header 重叠 */
  border-bottom: 1px solid var(--sa-border);
}

.sa-sidebar-title {
  font-size: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sa-sidebar-title-sub {
  font-size: 0.85rem;
  text-transform: none;
  letter-spacing: 0.05em;
  color: var(--sa-muted);
}

.sa-sidebar-close {
  background: none;
  border: none;
  color: var(--sa-muted);
  cursor: pointer;
  padding: 0.3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.sa-sidebar-close:hover {
  color: var(--sa-ink);
}

.sa-sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sa-sidebar-new-search-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
}

.sa-sidebar-empty {
  text-align: center;
  color: var(--sa-muted);
  font-size: 0.85rem;
  padding: 2rem 1rem;
}

.sa-sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.sa-sidebar-item {
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

.sa-sidebar-item:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: rgba(163, 177, 138, 0.3);
}

.sa-sidebar-item--active {
  background: rgba(163, 177, 138, 0.15);
  border-color: rgba(163, 177, 138, 0.4);
}

.sa-sidebar-item-title {
  font-size: 0.85rem;
  color: var(--sa-ink);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.sa-sidebar-item-time {
  font-size: 0.72rem;
  color: var(--sa-muted);
}

.sa-lab-header {
  text-align: center !important;
  margin: 0 auto !important;
  margin-bottom: 1rem;
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  display: flex;
  flex-direction: column;
  align-items: center !important;
  justify-content: center;
  padding: 0 !important;
}

.sa-lab-title {
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 400;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
  line-height: 1.2;
}

.sa-lab-title-sub {
  font-size: 0.4em;
  font-family: var(--sa-font-sans);
  font-weight: 300;
  letter-spacing: 0.1em;
  text-transform: none;
  margin-left: 0.5em;
}

.sa-lab-subtitle {
  font-size: clamp(0.9rem, 1.5vw, 1.1rem);
  color: var(--sa-muted);
  margin-top: 1rem;
  font-family: var(--sa-font-serif);
  font-style: italic;
}

.sa-lab-search-form {
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  min-width: 0;
  margin: 0 auto !important;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0 !important;
  float: none !important;
  clear: both !important;
  position: relative !important;
  box-sizing: border-box;
}

.sa-lab-search-field {
  display: flex;
  gap: 1rem;
  align-items: stretch;
  width: 100%;
}

.sa-lab-search-input {
  flex: 1;
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  min-width: 0;
  height: 64px !important;
  padding: 0 24px !important;
  background: transparent !important;
  border: 1px solid var(--sa-border);
  border-radius: 12px !important;
  font-size: clamp(0.9rem, 1.5vw, 1.1rem) !important; /* 与副标题字体大小一致，使用 !important 确保生效 */
  font-family: var(--sa-font-sans);
  color: var(--sa-ink);
  text-align: left !important;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.sa-lab-search-input:focus {
  outline: none;
  border-color: var(--sa-sage);
  background: transparent !important; /* 移除背景色 */
  box-shadow: none; /* 移除阴影 */
}

.sa-lab-search-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sa-lab-search-btn {
  white-space: nowrap;
  height: 64px !important;
  padding: 0 2rem !important;
  min-width: 0 !important; /* 强制解除宽度限制 */
  border-radius: 12px !important;
  font-size: 1.2rem !important;
}

/* Loading State */
.sa-lab-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 4rem 2rem;
  min-height: 300px;
}

.sa-lab-loading-spinner {
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

.sa-lab-loading-text {
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.9rem;
  color: var(--sa-muted);
  letter-spacing: 0.1em;
}

/* 3. 结果区域：确保横向排列，支持换行 */
.sa-lab-analysis-results {
  width: 100% !important; /* 使用百分比，避免溢出 */
  max-width: 100% !important; /* 使用 100%，由父容器控制 padding */
  min-width: 0 !important; /* 允许缩小 */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  margin: 0 auto !important; /* 居中 */
  padding: 0 !important; /* 移除 padding，由父容器控制 */
  box-sizing: border-box;
  position: relative;
  z-index: 1; /* 降低 z-index */
  overflow: visible; /* 确保内容不被截断 */
}

.sa-lab-results-grid {
  /* --- 核心修复：使用 Grid 代替 Flex --- */
  display: grid;
  
  /* 魔法代码：自动计算列数 */
  /* 翻译：每列最小 380px，空间足够时平分剩余宽度 (1fr) */
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  
  gap: 30px;           /* 卡片之间的间距 */
  width: 100%;         /* 占满容器 */
  align-items: start;  /* 顶部对齐 */
  padding: 0 0 50px 0; /* 移除左右 padding，由父容器控制；底部留白，防止贴底 */
  box-sizing: border-box;
  position: relative;
  z-index: 1; /* 降低 z-index */
}

/* Result Card Base Style */
.sa-lab-result-card {
  background: transparent !important; /* 移除背景色 */
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.1); /* 保留边框 */
  display: flex;
  flex-direction: column;
  width: 100%;         /* 让 Grid 控制宽度 */
  height: 100%;        /* 填满 Grid 格子 */
  box-sizing: border-box;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
  position: relative;
  z-index: 1; /* 降低 z-index */
}

/* 三列等高卡片 */
.sa-lab-radar-card,
.sa-lab-overview-card,
.sa-lab-data-card {
  width: 100%;         /* 让 Grid 控制宽度 */
  height: 100%;        /* 填满 Grid 格子 */
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  z-index: 1; /* 降低 z-index */
}

.sa-lab-card-title {
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
  font-size: 1.1rem;
  font-weight: 400;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0 0 1.5rem 0;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--sa-border);
  text-align: left;
  width: 100%;
}

.sa-lab-card-content {
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  max-height: 500px;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

.sa-lab-info-item {
  text-align: left;
  line-height: 1.8;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

.sa-lab-info-item strong {
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
  font-weight: 600;
}

.sa-lab-info-item--alert {
  color: var(--sa-rose);
}

.sa-lab-notes-section {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.sa-lab-note-row {
  text-align: left;
  line-height: 1.8;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

.sa-lab-note-row strong {
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
  font-weight: 600;
}



.sa-lab-chart-container {
  height: 400px;
  position: relative;
  width: 100% !important;
  max-width: none !important; /* 强制解除宽度限制 */
  padding: 1rem;
  box-sizing: border-box;
}

.sa-lab-chart {
  width: 100% !important;
  height: 100% !important;
}

.sa-lab-chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.9rem;
  color: var(--sa-muted);
}


/* 自定义滚动条 */
.sa-lab-card-content::-webkit-scrollbar {
  width: 6px;
}

.sa-lab-card-content::-webkit-scrollbar-track {
  background: rgba(163, 177, 138, 0.1);
  border-radius: 3px;
}

.sa-lab-card-content::-webkit-scrollbar-thumb {
  background: rgba(163, 177, 138, 0.3);
  border-radius: 3px;
}

.sa-lab-card-content::-webkit-scrollbar-thumb:hover {
  background: rgba(163, 177, 138, 0.5);
}

.sa-lab-data-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.sa-lab-data-item--full {
  margin-top: 0.5rem;
}

.sa-lab-data-item--notes {
  margin-top: 1rem;
}

/* 香调表（金字塔式） */
.sa-lab-notes-pyramid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.5rem;
}

.sa-lab-note-item {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  padding: 0.6rem 0;
  border-bottom: 1px solid rgba(163, 177, 138, 0.1);
}

.sa-lab-note-item:last-child {
  border-bottom: none;
}

.sa-lab-note-label {
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.75rem;
  color: var(--sa-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  min-width: 3rem;
  flex-shrink: 0;
}

.sa-lab-note-value {
  font-size: 0.85rem;
  color: var(--sa-ink);
  line-height: 1.5;
  flex: 1;
}

/* 相似推荐列表 */
.sa-lab-similar-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

.sa-lab-similar-list li {
  font-size: 0.9rem;
  color: var(--sa-ink);
  line-height: 1.6;
  padding: 0;
  margin: 0;
  text-align: left;
  word-wrap: break-word;
  word-break: break-word;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

/* 参考信源列表 */
.sa-lab-reference-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-family: "Songti SC", "Noto Serif SC", "STSong", "SimSun", serif; /* 宋体 */
}

.sa-lab-reference-list li {
  font-size: 0.9rem;
  line-height: 1.6;
  padding: 0;
  margin: 0;
  text-align: left;
  word-wrap: break-word;
  word-break: break-word;
}

.sa-lab-reference-link {
  color: var(--sa-sage);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  transition: color 0.2s, text-decoration 0.2s;
  word-break: break-all;
}

.sa-lab-reference-link:hover {
  color: var(--sa-sage-dark);
  text-decoration: underline;
}

.sa-lab-reference-link svg {
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.sa-lab-reference-link:hover svg {
  opacity: 1;
}

.sa-lab-data-label {
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.75rem;
  color: var(--sa-muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sa-lab-data-value {
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.9rem;
  color: var(--sa-ink);
  line-height: 1.6;
}

.sa-lab-safety-text {
  font-size: 0.85rem;
  line-height: 1.7;
}

.sa-lab-source {
  text-align: center;
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 0.7rem;
  color: var(--sa-muted);
  padding-top: 1rem;
  border-top: 1px dashed var(--sa-border);
}

/* Not Found State */
.sa-lab-not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 4rem 2rem;
}

.sa-lab-not-found-content {
  text-align: center;
  max-width: none !important; /* 强制解除宽度限制 */
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sa-lab-not-found-title {
  font-size: 2rem;
  font-weight: 400;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
}

.sa-lab-not-found-text {
  font-size: 1rem;
  color: var(--sa-muted);
  line-height: 1.7;
  font-style: italic;
  margin: 0;
}

.sa-lab-create-btn {
  margin-top: 1rem;
  padding: 0.9rem 2.5rem;
  font-size: 0.95rem;
}

/* Responsive */
@media (max-width: 1024px) {
  .sa-lab-results-grid {
    grid-template-columns: 1fr !important; /* 单列布局 */
    width: 100% !important;
    gap: 20px !important; /* 移动端减小间距 */
    padding: 0 1rem 30px 1rem !important;
  }
  
  .sa-lab-radar-card,
  .sa-lab-overview-card,
  .sa-lab-data-card {
    width: 100% !important;
    height: auto !important; /* 移动端允许高度自适应 */
  }
  
  .sa-lab-chart-container {
    height: 300px;
  }
  
  .sa-lab-card-content {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .sa-lab-root {
    height: 100vh;
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
    overflow: hidden;
  }
  
  .sa-lab-main-scroll-area {
    margin-top: 0 !important; /* 移除顶部间距，让内容从顶部开始 */
    padding-left: 0;
  }
  
  .sa-lab-content-direct {
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
    min-height: 100vh; /* 占满整个视口 */
    padding-top: 0.5rem !important; /* 最小化顶部间距 */
    padding-left: 0.5rem !important; /* 大幅减少左侧间距 */
    padding-right: 0.5rem !important; /* 大幅减少右侧间距 */
    padding-bottom: 3vh;
  }
  
  .sa-lab-content-direct--has-data {
    padding-top: 3px !important; /* 移动端几乎贴近顶部 */
  }
  
  .sa-sidebar-toggle-btn {
    top: 5px; /* 移动端也几乎贴近顶部 */
  }
  
  .sa-sidebar {
    top: 0; /* 移动端也从顶部开始 */
  }
  
  .sa-sidebar-header {
    padding-top: calc(56px + 1.2rem); /* 移动端 header 可能更矮 */
  }
  
  .sa-lab-search-form {
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
    padding: 0 !important; /* 完全移除内边距 */
    margin: 0;
  }
  
  .sa-lab-search-field {
    width: 100% !important;
    padding: 0 !important;
    margin: 0;
  }
  
  .sa-lab-search-input {
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
    height: 52px !important;
    font-size: 15px !important; /* 固定字体大小，避免过小 */
    font-weight: 400 !important;
    line-height: 1.6 !important;
    padding: 0 1rem !important; /* 只在输入框内部留边距 */
    border-radius: 8px !important;
  }

  .sa-lab-search-btn {
    width: 100% !important;
    margin-top: 0.5rem;
  }
  
  .sa-lab-search-field {
    flex-direction: column;
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
  }
  
  .sa-lab-search-btn {
    width: 100% !important;
    max-width: none !important; /* 强制解除宽度限制 */
    height: 56px !important;
    font-size: 1rem !important;
  }
  
  .sa-lab-results-grid {
    grid-template-columns: 1fr !important; /* 单列布局 */
    width: 100% !important;
    gap: 12px !important; /* 进一步减小间距 */
    padding: 0 !important; /* 完全移除内边距 */
    margin: 0;
  }
  
  .sa-lab-radar-card,
  .sa-lab-overview-card,
  .sa-lab-data-card {
    width: 100% !important;
    height: auto !important; /* 移动端允许高度自适应 */
    padding: 1rem 0.75rem !important; /* 大幅减少卡片内边距 */
    margin: 0 !important;
    border-radius: 8px !important;
  }
  
  .sa-lab-card-content {
    max-height: 400px;
    font-size: 15px !important;
    line-height: 1.7 !important;
    font-weight: 400 !important;
  }

  /* 优化标题和文字 */
  .sa-lab-title {
    font-size: clamp(2rem, 8vw, 3rem) !important;
    font-weight: 500 !important;
    line-height: 1.2 !important;
  }

  .sa-lab-subtitle {
    font-size: 0.9rem !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
  }

  .sa-lab-card-title {
    font-size: 1rem !important;
    font-weight: 500 !important;
  }

  .sa-lab-info-item,
  .sa-lab-note-row {
    font-size: 15px !important;
    font-weight: 400 !important;
    line-height: 1.7 !important;
  }
}

/* Dark Mode */
:global(.dark) .sa-lab-title,
:global(.dark) .sa-lab-panel-title,
:global(.dark) .sa-lab-not-found-title {
  color: #f5f1ea !important;
}

:global(.dark) .sa-lab-subtitle,
:global(.dark) .sa-lab-loading-text,
:global(.dark) .sa-lab-source,
:global(.dark) .sa-lab-data-label,
:global(.dark) .sa-lab-not-found-text {
  color: rgba(245, 241, 234, 0.7) !important;
}

:global(.dark) .sa-lab-data-value {
  color: #f5f1ea !important;
}

:global(.dark) .sa-lab-search-input {
  background: transparent !important; /* 移除背景色 */
  border-color: var(--sa-border);
  color: #f5f1ea;
}

:global(.dark) .sa-lab-search-input:focus {
  background: transparent !important; /* 移除背景色 */
  border-color: rgba(163, 177, 138, 0.6);
}

:global(.dark) .sa-lab-result-card {
  background: transparent !important; /* 移除背景色 */
  border-color: var(--sa-border);
}
</style>

