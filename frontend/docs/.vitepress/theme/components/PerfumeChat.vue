<template>
  <section class="sa-chat-root" :class="{ 'sa-chat-root--with-memo': conversationMemo }">
    <!-- 侧边栏按钮（左上角，对话框外） -->
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
          <span v-if="locale === 'zh'">对话历史</span>
          <span v-else>Conversations</span>
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
        <button
          class="sa-sidebar-new-btn sa-btn sa-btn--sage"
          type="button"
          @click="startNewConversation"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 3v10M3 8h10"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
          <span v-if="locale === 'zh'">开启新对话</span>
          <span v-else>New Conversation</span>
        </button>
        <div class="sa-sidebar-list">
          <button
            v-for="conv in conversations"
            :key="conv.id"
            class="sa-sidebar-item"
            :class="{ 'sa-sidebar-item--active': selectedConversationId === conv.id }"
            type="button"
            @click="selectConversation(conv.id)"
          >
            <div class="sa-sidebar-item-title">{{ conv.title }}</div>
            <div class="sa-sidebar-item-time">{{ formatConversationTime(conv.updated_at) }}</div>
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

    <!-- 主内容区域：聊天界面和手札 -->
    <div class="sa-main-wrapper" :class="{ 'sa-main-wrapper--with-memo': conversationMemo }">
      <div class="sa-chat-shell sa-morandi-card">
        <header class="sa-chat-header">
          <div class="sa-chat-title-block">
            <p class="sa-chat-eyebrow sa-serif">
              <span v-if="locale === 'zh'">Le Nez</span>
              <span v-else>Le Nez</span>
            </p>
          <h2 class="sa-chat-title sa-serif">
            <span v-if="locale === 'zh'">Scent Alchemist</span>
            <span v-else>Scent Alchemist</span>
            <span class="sa-chat-title-sub">
              <span v-if="locale === 'zh'">｜气味炼金术士</span>
              <span v-else>｜Your Private Perfumer</span>
            </span>
          </h2>
          <p class="sa-chat-subtitle">
            <span v-if="locale === 'zh'">
              像在巴黎沙龙写一封信，告诉我你的此刻心情与想携带的香气。
            </span>
            <span v-else>
              As if writing a letter in a Parisian salon—tell me your mood and the scent you wish to carry.
            </span>
          </p>
        </div>

        <div class="sa-chat-controls">
          <button
            class="sa-btn sa-btn--ghost sa-chat-lang-toggle"
            type="button"
            @click="toggleLocale"
          >
            <span v-if="locale === 'zh'">中 / English</span>
            <span v-else>EN / 中文</span>
          </button>
        </div>
      </header>

      <div class="sa-chat-body">
        <div class="sa-chat-paper sa-scrollbar" ref="chatPaperRef">
          <div class="sa-chat-paper-gradient" />

          <div class="sa-chat-thread">
            <article
              v-for="(msg, index) in messages"
              :key="index"
              class="sa-chat-entry"
              :data-role="msg.role"
            >
              <div class="sa-chat-entry-meta">
                <span class="sa-chat-entry-role sa-serif">
                  <span v-if="msg.role === 'user'">
                    <span v-if="locale === 'zh'">来信人</span>
                    <span v-else>Correspondent</span>
                  </span>
                  <span v-else>
                    <span v-if="locale === 'zh'">调香师</span>
                    <span v-else>Perfumer</span>
                  </span>
                </span>
                <span class="sa-chat-entry-divider">—</span>
                <span class="sa-chat-entry-time">
                  {{ msg.timestamp }}
                </span>
              </div>
              <div
                class="sa-chat-entry-text"
                v-html="renderMarkdown(msg.text)"
              />
              <!-- Distill Visuals 按钮 - 只在助手消息显示 -->
              <div v-if="msg.role === 'assistant'" class="sa-chat-entry-actions">
                <button
                  class="sa-chat-distill-btn"
                  type="button"
                  @click="handleDistillVisuals(msg.text)"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M8 2L3 5V11L8 14L13 11V5L8 2Z"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      d="M3 5L8 8L13 5"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                    <path
                      d="M8 8V14"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <span v-if="locale === 'zh'">⚗️ 凝结视觉</span>
                  <span v-else>⚗️ Distill Visuals</span>
                </button>
              </div>
            </article>

            <p v-if="messages.length === 0" class="sa-chat-placeholder sa-muted">
              <span v-if="locale === 'zh'">
                写下你的心情、场景或记忆碎片，让气味替你完成一首短诗。
              </span>
              <span v-else>
                Describe your mood, a scene, or a fragment of memory—let scent finish the poem for you.
              </span>
            </p>
          </div>
        </div>
      </div>

      <footer class="sa-chat-footer">
        <form class="sa-chat-form" @submit.prevent="handleSubmit">
          <label class="sa-chat-label sa-serif" for="sa-chat-input">
            <span v-if="locale === 'zh'">写一封给调香师的信</span>
            <span v-else>Write a letter to your perfumer</span>
          </label>

          <div class="sa-chat-input-row">
            <textarea
              id="sa-chat-input"
              v-model="currentInput"
              class="sa-chat-input sa-scrollbar"
              :placeholder="placeholderText"
              :disabled="loading"
              rows="3"
            />
          </div>

          <div class="sa-chat-actions">
            <div class="sa-chat-hint sa-muted">
              <span v-if="locale === 'zh'">
                例如：「下雨的夜晚，独自走在河岸边」或「第一次去巴黎见旧友」。
              </span>
              <span v-else>
                For example: “A rainy night alone by the river” or “First time meeting an old friend in Paris”.
              </span>
            </div>

            <button
              class="sa-btn sa-btn--sage sa-chat-submit"
              type="submit"
              :disabled="loading || currentInput.trim().length === 0"
            >
              <span v-if="!loading">
                <span v-if="locale === 'zh'">寄出信笺</span>
                <span v-else>Send the letter</span>
              </span>
              <span v-else class="sa-chat-spinner-text">
                <span v-if="locale === 'zh'">正在调配香气…</span>
                <span v-else>Blending your accord…</span>
              </span>
            </button>
          </div>
        </form>
      </footer>
      </div>

      <!-- Le Nez先生的手札（右侧独立面板） -->
      <aside v-if="conversationMemo" class="sa-memo-panel sa-morandi-card">
        <div class="sa-memo-header">
          <h3 class="sa-memo-title sa-serif">
            <span v-if="locale === 'zh'">Le Nez 先生的手札</span>
            <span v-else>Le Nez's Memo</span>
          </h3>
        </div>
        <div class="sa-memo-content sa-scrollbar">
          <div class="sa-memo-text" v-html="renderMarkdown(conversationMemo)"></div>
        </div>
      </aside>
    </div>

    <!-- 名字输入弹窗 -->
    <div v-if="showNameModal" class="sa-modal-overlay" @click.self="handleNameModalClose">
      <div class="sa-modal sa-morandi-card">
        <div class="sa-modal-header">
          <h3 class="sa-modal-title sa-serif">
            <span v-if="locale === 'zh'">初次见面</span>
            <span v-else>First Meeting</span>
          </h3>
        </div>
        <div class="sa-modal-body">
          <p class="sa-modal-intro">
            <span v-if="locale === 'zh'">
              <strong>我是 Le Nez，一位来自法国的调香师。</strong>
              <br />
              像在巴黎沙龙写一封信，告诉我你的此刻心情与想携带的香气。
            </span>
            <span v-else>
              <strong>I am Le Nez, a perfumer from France.</strong>
              <br />
              As if writing a letter in a Parisian salon—tell me your mood and the scent you wish to carry.
            </span>
          </p>
          <div class="sa-modal-input-group">
            <label class="sa-modal-label sa-serif" for="sa-name-input">
              <span v-if="locale === 'zh'">请问，我该如何称呼你？</span>
              <span v-else>May I ask, how should I address you?</span>
            </label>
            <input
              id="sa-name-input"
              v-model="userNameInput"
              type="text"
              class="sa-modal-input"
              :placeholder="locale === 'zh' ? '请输入你的名字' : 'Please enter your name'"
              @keyup.enter="handleNameSubmit"
              autofocus
            />
          </div>
        </div>
        <div class="sa-modal-footer">
          <button
            class="sa-btn sa-btn--sage sa-modal-submit"
            type="button"
            @click="handleNameSubmit"
            :disabled="!userNameInput.trim()"
          >
            <span v-if="locale === 'zh'">开始对话</span>
            <span v-else>Start Conversation</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import MarkdownIt from "markdown-it";
import { API_BASE_URL } from '../../../../config';

type Role = "user" | "assistant";
type Locale = "zh" | "en";

interface ChatMessage {
  role: Role;
  text: string;
  timestamp: string;
}

interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
}

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
});

const sanitizeMarkdown = (text: string): string => {
  // 简单去除「单数次出现」的 **，避免模型输出残留符号
  const lines = text.split(/\r?\n/);
  const processed = lines.map((line) => {
    const count = (line.match(/\*\*/g) || []).length;
    if (count % 2 === 1) {
      return line.replace(/\*\*/g, "");
    }
    return line;
  });
  return processed.join("\n");
};

const renderMarkdown = (text: string) => {
  return md.render(sanitizeMarkdown(text));
};

// 从 localStorage 读取语言设置，如果没有则默认为中文
const getStoredLocale = (): Locale => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("leNez_locale");
    if (stored === "zh" || stored === "en") {
      return stored as Locale;
    }
  }
  return "zh";
};

const locale = ref<Locale>(getStoredLocale());
const currentInput = ref("");
const messages = ref<ChatMessage[]>([]);
const loading = ref(false);
const chatPaperRef = ref<HTMLElement | null>(null);
const conversationId = ref<string | null>(null);
const conversations = ref<ConversationSummary[]>([]);
const selectedConversationId = ref<string>("");
const sidebarOpen = ref(false);
const hasStartedConversation = ref(false);
const conversationMemo = ref<string | null>(null);
const showNameModal = ref(false);
const userNameInput = ref("");
const userName = ref<string | null>(null);

const placeholderText = computed(() => {
  if (locale.value === "zh") {
    return "此刻的你，像什么味道？写几句给你的气味炼金术士。";
  }
  return "If this moment were a scent, how would it smell? Write a few lines to your scent alchemist.";
});

const formatTime = () => {
  const now = new Date();
  return now.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const toggleLocale = () => {
  locale.value = locale.value === "zh" ? "en" : "zh";
  // 保存语言设置到 localStorage
  if (typeof window !== "undefined") {
    localStorage.setItem("leNez_locale", locale.value);
  }
  // 切换语言后重新加载会话列表以获取对应语言的摘要
  loadConversations();
  // 如果当前有打开的会话，重新加载以获取对应语言的手札
  if (conversationId.value) {
    loadConversationDetail(conversationId.value);
  }
};

const generateConversationId = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const loadConversations = async () => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/conversations?locale=${locale.value}`
    );
    if (!response.ok) return;
    const data: ConversationSummary[] = await response.json();
    conversations.value = data;
  } catch (error) {
    console.error(error);
  }
};

const loadConversationDetail = async (id: string) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/conversations/${encodeURIComponent(id)}?locale=${locale.value}`,
    );
    if (!response.ok) return;
    const data: { 
      id: string; 
      messages: { role: Role; content: string }[];
      memo?: string;
      user_name?: string;
    } = await response.json();
    conversationId.value = data.id;
    messages.value = data.messages.map((m) => ({
      role: m.role,
      text: m.content,
      timestamp: formatTime(),
    }));
    conversationMemo.value = data.memo || null;
    // 如果会话中有用户名字，保存它
    if (data.user_name) {
      userName.value = data.user_name;
    }
    hasStartedConversation.value = true;
  } catch (error) {
    console.error(error);
  }
};

const handleNameModalClose = () => {
  // 不允许关闭，必须输入名字
};

const handleNameSubmit = () => {
  const name = userNameInput.value.trim();
  if (!name) return;
  
  userName.value = name;
  // 保存到本地存储
  localStorage.setItem("leNez_userName", name);
  showNameModal.value = false;
  hasStartedConversation.value = true;
};


const startNewConversation = () => {
  conversationId.value = null;
  selectedConversationId.value = "";
  messages.value = [];
  hasStartedConversation.value = false;
  conversationMemo.value = null;
  sidebarOpen.value = false;
  // 检查是否需要显示名字弹窗
  if (!userName.value) {
    showNameModal.value = true;
    userNameInput.value = "";
  }
};

const selectConversation = async (id: string) => {
  selectedConversationId.value = id;
  await loadConversationDetail(id);
  hasStartedConversation.value = true;
  sidebarOpen.value = false;
};

const handleConversationSelect = async () => {
  if (!selectedConversationId.value) {
    startNewConversation();
    return;
  }
  await selectConversation(selectedConversationId.value);
};

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

// 跳转到画室页面并传递消息内容
const handleDistillVisuals = (messageText: string) => {
  // 使用 URL 参数传递消息内容
  const encodedText = encodeURIComponent(messageText);
  window.location.href = `/atelier?extract_from=${encodedText}`;
};

// 强制应用/清除深色模式样式（不受 VitePress 限制）
const forceDarkModeStyles = () => {
  const isDark = document.documentElement.classList.contains("dark");

  // 对话框
  const chatPaper = document.querySelector(".sa-chat-paper");
  if (chatPaper) {
    if (isDark) {
      (chatPaper as HTMLElement).style.setProperty("background", "#4a4a4a", "important");
      const allTextElements = chatPaper.querySelectorAll("p, span, div, strong, em, a, li, ul, ol, h1, h2, h3, h4, h5, h6, .sa-chat-entry-text, .sa-chat-entry-text *");
      allTextElements.forEach((el) => {
        (el as HTMLElement).style.setProperty("color", "#f5f1ea", "important");
      });
    } else {
      // 白天模式：清除内联样式，恢复 CSS 默认样式
      (chatPaper as HTMLElement).style.removeProperty("background");
      const allTextElements = chatPaper.querySelectorAll("p, span, div, strong, em, a, li, ul, ol, h1, h2, h3, h4, h5, h6, .sa-chat-entry-text, .sa-chat-entry-text *");
      allTextElements.forEach((el) => {
        (el as HTMLElement).style.removeProperty("color");
      });
    }
  }

  // 手札面板
  const memoPanel = document.querySelector(".sa-memo-panel");
  if (memoPanel) {
    if (isDark) {
      (memoPanel as HTMLElement).style.setProperty("background", "#4a4a4a", "important");
      const allTextElements = memoPanel.querySelectorAll("p, span, div, strong, em, a, li, ul, ol, h1, h2, h3, h4, h5, h6, .sa-memo-text, .sa-memo-text *");
      allTextElements.forEach((el) => {
        (el as HTMLElement).style.setProperty("color", "#f5f1ea", "important");
      });
    } else {
      // 白天模式：清除内联样式，恢复 CSS 默认样式
      (memoPanel as HTMLElement).style.removeProperty("background");
      const allTextElements = memoPanel.querySelectorAll("p, span, div, strong, em, a, li, ul, ol, h1, h2, h3, h4, h5, h6, .sa-memo-text, .sa-memo-text *");
      allTextElements.forEach((el) => {
        (el as HTMLElement).style.removeProperty("color");
      });
    }
  }

  // 输入框
  const inputRow = document.querySelector(".sa-chat-input-row");
  if (inputRow) {
    if (isDark) {
      (inputRow as HTMLElement).style.setProperty("background", "#4a4a4a", "important");
    } else {
      // 白天模式：清除内联样式
      (inputRow as HTMLElement).style.removeProperty("background");
    }
  }
  const inputs = document.querySelectorAll(".sa-chat-input");
  inputs.forEach((input) => {
    if (isDark) {
      (input as HTMLElement).style.setProperty("background", "transparent", "important");
      (input as HTMLElement).style.setProperty("color", "#f5f1ea", "important");
    } else {
      // 白天模式：清除内联样式，恢复 CSS 默认样式
      (input as HTMLElement).style.removeProperty("background");
      (input as HTMLElement).style.removeProperty("color");
    }
  });
};

let styleObserver: MutationObserver | null = null;
let darkModeObserver: MutationObserver | null = null;

onMounted(() => {
  loadConversations();
  // 检查本地存储是否有用户名字
  const storedName = localStorage.getItem("leNez_userName");
  if (storedName) {
    userName.value = storedName;
  
  // 检查 URL 参数中是否有 initial_topic（从 Lab 页面跳转过来）
  const params = new URLSearchParams(window.location.search);
  const initialTopic = params.get("initial_topic");
  if (initialTopic && userName.value) {
    // 如果有初始话题且用户已登录，自动发送消息
    const decodedTopic = decodeURIComponent(initialTopic);
    currentInput.value = decodedTopic;
    // 延迟一下，确保界面已加载
    setTimeout(() => {
      handleSubmit();
    }, 500);
  }
  } else {
    // 如果没有名字，显示名字输入弹窗
    showNameModal.value = true;
  }

  // 强制应用深色模式样式
  nextTick(() => {
    forceDarkModeStyles();
    // 监听 DOM 变化，确保新添加的内容也应用样式
    styleObserver = new MutationObserver(() => {
      forceDarkModeStyles();
    });
    styleObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class"],
    });

    // 监听深色模式切换
    darkModeObserver = new MutationObserver(() => {
      forceDarkModeStyles();
    });
    darkModeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });
  });
});

onUnmounted(() => {
  if (styleObserver) {
    styleObserver.disconnect();
  }
  if (darkModeObserver) {
    darkModeObserver.disconnect();
  }
});

watch(
  () => messages.value,
  async () => {
    await nextTick();
    const container = chatPaperRef.value;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  },
  { deep: true },
);

const handleSubmit = async () => {
  const text = currentInput.value.trim();
  if (!text || loading.value) return;

  // 如果还没有输入名字，先显示名字弹窗
  if (!userName.value) {
    showNameModal.value = true;
    return;
  }

  const userMessage: ChatMessage = {
    role: "user",
    text,
    timestamp: formatTime(),
  };
  messages.value = [...messages.value, userMessage];
  currentInput.value = "";
  hasStartedConversation.value = true;

  if (!conversationId.value) {
    const newId = generateConversationId();
    conversationId.value = newId;
    selectedConversationId.value = newId;
    // 前端先行追加到本地会话列表，方便立即切换
    conversations.value = [
      {
        id: newId,
        title: text.slice(0, 40),
        updated_at: new Date().toISOString(),
      },
      ...conversations.value,
    ];
  }

  loading.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: [
          // 将当前本地对话历史转换成 LLM 所需的 role/content 结构
          ...messages.value.map((m) => ({
            role: m.role,
            content: m.text,
          })),
        ],
        locale: locale.value,
        conversation_id: conversationId.value,
        user_name: userName.value || undefined,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    // 先插入一个空的助手消息，用于打字机式逐步填充
    const assistantMessage: ChatMessage = {
      role: "assistant",
      text: "",
      timestamp: formatTime(),
    };
    messages.value = [...messages.value, assistantMessage];

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Readable stream not supported");
    }

    const decoder = new TextDecoder("utf-8");
    let accumulated = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (!chunk) continue;

      accumulated += chunk;

      // 更新最后一条助手消息的文本，触发响应式刷新
      const lastIndex = messages.value.length - 1;
      const last = messages.value[lastIndex];
      if (last && last.role === "assistant") {
        messages.value = [
          ...messages.value.slice(0, lastIndex),
          { ...last, text: accumulated },
        ];
      }
    }
  } catch (error) {
    const fallback: ChatMessage = {
      role: "assistant",
      text:
        locale.value === "zh"
          ? "调香师今天有些忙乱，暂时未能回应。但你的心情我已经轻轻收下。"
          : "The perfumer is a little scattered today and could not respond properly, but your mood has been quietly noted.",
      timestamp: formatTime(),
    };
    messages.value = [...messages.value, fallback];
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.sa-chat-root {
  position: relative;
  width: 100%;
  min-height: calc(100vh - 4rem);
  padding: 2rem 0;
  overflow-x: visible;
}

.sa-chat-root--with-memo {
  padding-left: 0;
  padding-right: 0;
  overflow-x: visible;
}

/* 侧边栏按钮（左上角） */
.sa-sidebar-toggle-btn {
  position: fixed;
  top: 1.5rem;
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

/* 主内容包装器 */
.sa-main-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 0;
  width: 100%;
  margin: 0 auto;
  padding: 0;
  transition: all 0.3s ease-out;
}

/* 没有手札时，聊天界面居中，至少占屏幕50% */
.sa-main-wrapper:not(.sa-main-wrapper--with-memo) {
  padding: 0 2rem;
}

.sa-main-wrapper:not(.sa-main-wrapper--with-memo) .sa-chat-shell {
  max-width: 1000px;
  width: 100%;
  min-width: 50%;
  margin: 0 auto;
}

.sa-chat-shell {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 900px;
  width: 100%;
  padding: 2rem 2.2rem 2rem;
  position: relative;
  overflow: visible;
  transition: all 0.3s ease-out;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 4rem);
}

/* 有手札时，整个布局移动到左边 */
.sa-main-wrapper--with-memo {
  justify-content: flex-start;
  padding: 0;
  gap: 0;
  align-items: flex-start;
  margin-left: 0;
  width: 100%;
}

/* 有手札时，对话框占屏幕50%，从左边开始 */
.sa-main-wrapper--with-memo .sa-chat-shell {
  flex: 0 0 50vw;
  max-width: 50vw;
  width: 50vw;
  min-width: 50vw;
  padding: 2rem 2.2rem 2rem;
  margin-left: 0;
  margin-right: 70px;
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 4rem);
  overflow: visible;
  box-sizing: border-box;
}

.sa-chat-shell::before {
  content: "";
  position: absolute;
  inset: -80px;
  background:
    radial-gradient(circle at 0% 0%, rgba(188, 173, 160, 0.23), transparent 60%),
    radial-gradient(circle at 100% 100%, rgba(163, 177, 138, 0.25), transparent 55%);
  mix-blend-mode: soft-light;
  opacity: 0.72;
  pointer-events: none;
}

.sa-chat-header,
.sa-chat-footer,
.sa-chat-body {
  position: relative;
  z-index: 1;
}

.sa-chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.4rem;
}

.sa-chat-header .sa-chat-title-block {
  display: flex;
  flex-direction: column;
}

.sa-chat-header .sa-chat-controls {
  display: flex;
  align-items: flex-start;
  padding-top: 0;
  margin-top: 0.35rem;
}

.sa-chat-title-block {
  flex: 1;
  min-width: 0;
  position: relative;
}

.sa-chat-eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--sa-muted);
  margin-bottom: 0.35rem;
}

.sa-chat-title {
  font-size: 1.6rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0;
  color: var(--sa-ink);
  display: inline-block;
  white-space: nowrap;
}

.sa-chat-title-sub {
  font-size: 0.9rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-left: 0.4rem;
  color: var(--sa-muted);
  display: inline;
}

.sa-chat-subtitle {
  margin-top: 0.5rem;
  margin-bottom: 0;
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--sa-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .sa-chat-subtitle {
    white-space: normal;
  }
}

.sa-chat-controls {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  flex-shrink: 0;
}

.sa-chat-history-select {
  font-size: 0.74rem;
  padding-inline: 0.4rem;
  padding-block: 0.3rem;
  border-radius: 999px;
  border: 1px solid rgba(196, 186, 172, 0.8);
  background: rgba(251, 248, 242, 0.9);
  color: var(--sa-muted);
  font-family: var(--sa-font-sans);
  appearance: none;
}

.sa-chat-lang-toggle {
  font-size: 0.74rem;
  padding-inline: 0.9rem;
  padding-block: 0.38rem;
}

.sa-chat-body {
  margin-bottom: 1.1rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.sa-chat-paper {
  position: relative;
  background: linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.9),
      rgba(245, 242, 236, 0.92)
    ),
    repeating-linear-gradient(
      to bottom,
      rgba(214, 207, 194, 0.4),
      rgba(214, 207, 194, 0.4) 1px,
      transparent 1px,
      transparent 26px
    );
  border-radius: 14px;
  border: 1px solid rgba(196, 186, 172, 0.5);
  padding: 1.1rem 1.1rem 1rem;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  max-height: 100%;
}

.sa-chat-paper-gradient {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at top left,
    rgba(196, 154, 156, 0.2) 0,
    transparent 60%
  );
  mix-blend-mode: soft-light;
  pointer-events: none;
}

.sa-chat-thread {
  position: relative;
  z-index: 1;
}

.sa-chat-entry {
  margin-bottom: 1.1rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px dashed rgba(196, 186, 172, 0.5);
}

.sa-chat-entry:last-child {
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 0.3rem;
}

.sa-chat-entry-meta {
  display: flex;
  align-items: baseline;
  font-size: 0.8rem;
  color: var(--sa-muted);
  margin-bottom: 0.2rem;
}

.sa-chat-entry-role {
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sa-chat-entry-divider {
  margin-inline: 0.5rem;
  opacity: 0.6;
}

.sa-chat-entry-time {
  font-variant-numeric: tabular-nums;
}

.sa-chat-entry-text {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--sa-ink);
}

.sa-chat-entry-text p {
  margin: 0 0 0.4rem;
  line-height: 1.7;
}

.sa-chat-entry-text p:last-child {
  margin-bottom: 0;
}

.sa-chat-entry-text strong {
  color: #2f2b25;
  font-weight: 600;
}

.sa-chat-entry-text ul,
.sa-chat-entry-text ol {
  margin: 0.2rem 0 0.4rem;
  padding-left: 1.1rem;
}

.sa-chat-entry-text li {
  margin: 0.1rem 0;
}

.sa-chat-entry-text hr {
  border: 0;
  border-top: 1px dashed rgba(196, 186, 172, 0.8);
  margin: 0.9rem 0 0.8rem;
}

.sa-chat-entry[data-role="assistant"] .sa-chat-entry-text {
  font-style: italic;
}

.sa-chat-entry-actions {
  margin-top: 0.8rem;
  display: flex;
  justify-content: flex-start;
}

.sa-chat-distill-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.9rem;
  background: transparent;
  border: 1px solid rgba(163, 177, 138, 0.4);
  border-radius: 999px;
  color: var(--sa-sage);
  font-size: 0.75rem;
  font-family: var(--sa-font-serif);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sa-chat-distill-btn:hover {
  background: rgba(163, 177, 138, 0.1);
  border-color: var(--sa-sage);
  transform: translateY(-1px);
}

.sa-chat-distill-btn svg {
  width: 14px;
  height: 14px;
  opacity: 0.8;
}

.sa-chat-placeholder {
  font-size: 0.86rem;
  text-align: center;
  padding-block: 0.4rem 0.2rem;
}

.sa-chat-footer {
  border-top: 1px solid rgba(196, 186, 172, 0.6);
  padding-top: 1rem;
  margin-top: 0.3rem;
}

.sa-chat-form {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.sa-chat-label {
  font-size: 0.8rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--sa-muted);
}

.sa-chat-input-row {
  border-radius: 12px;
  border: 1px solid rgba(196, 186, 172, 0.8);
  background: rgba(251, 248, 242, 0.92);
  padding: 0.5rem 0.7rem;
}

.sa-chat-input {
  width: 100%;
  border: none;
  resize: none;
  outline: none;
  background: transparent;
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--sa-ink);
  font-family: var(--sa-font-serif);
}

.sa-chat-input::placeholder {
  color: rgba(130, 126, 118, 0.7);
}

.sa-chat-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.sa-chat-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.sa-chat-hint {
  font-size: 0.78rem;
  line-height: 1.5;
  max-width: 480px;
}

.sa-chat-submit {
  white-space: nowrap;
}

.sa-chat-spinner-text {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

@media (max-width: 768px) {
  .sa-chat-shell {
    margin-inline: -0.4rem;
    border-radius: 0;
  }

  .sa-chat-header {
    flex-direction: column;
    align-items: stretch;
  }

  .sa-chat-controls {
    justify-content: flex-end;
  }

  .sa-chat-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .sa-chat-hint {
    order: 2;
  }

  .sa-chat-submit {
    align-self: flex-end;
    order: 1;
  }

  .sa-chat-content-wrapper {
    grid-template-columns: 1fr;
  }
}

/* 手札面板样式（右侧独立面板） */
.sa-memo-panel {
  flex: 0 0 375px;
  max-width: 375px;
  width: 375px;
  min-width: 375px;
  padding: 2rem 2.2rem 1.8rem;
  position: sticky;
  top: 2rem;
  align-self: flex-start;
  margin-left: 0;
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
  max-height: calc(100vh - 4rem); /* 与对话框相同的高度限制 */
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 隐藏面板本身的溢出，内容区域会滚动 */
  box-sizing: border-box;
  visibility: visible;
  opacity: 1;
}

.sa-memo-panel::before {
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

.sa-memo-header {
  margin-bottom: 0.8rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px dashed rgba(196, 186, 172, 0.5);
  position: relative;
  z-index: 1;
}

.sa-memo-title {
  font-size: 0.8rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--sa-muted);
  margin: 0;
  font-weight: 500;
}

.sa-memo-content {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.sa-memo-text {
  font-size: 0.85rem;
  line-height: 1.8;
  color: var(--sa-ink);
  font-style: italic;
  white-space: pre-wrap;
  font-family: var(--sa-font-serif);
}

.sa-memo-text p {
  margin: 0 0 0.6rem;
}

.sa-memo-text p:last-child {
  margin-bottom: 0;
}

/* 名字输入弹窗样式 */
.sa-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.sa-modal {
  max-width: 500px;
  width: 100%;
  padding: 2rem;
  position: relative;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.sa-modal-header {
  margin-bottom: 1.2rem;
}

.sa-modal-title {
  font-size: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
}

.sa-modal-body {
  margin-bottom: 1.5rem;
}

.sa-modal-intro {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--sa-ink);
  margin-bottom: 1.5rem;
}

.sa-modal-intro strong {
  color: var(--sa-ink);
  font-weight: 600;
}

.sa-modal-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.sa-modal-label {
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-muted);
}

.sa-modal-input {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  border: 1px solid rgba(196, 186, 172, 0.8);
  background: rgba(251, 248, 242, 0.92);
  font-size: 0.95rem;
  color: var(--sa-ink);
  font-family: var(--sa-font-sans);
  outline: none;
  transition: all 0.2s;
}

.sa-modal-input:focus {
  border-color: rgba(163, 177, 138, 0.6);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 3px rgba(163, 177, 138, 0.1);
}

.sa-modal-input::placeholder {
  color: rgba(130, 126, 118, 0.6);
}

.sa-modal-footer {
  display: flex;
  justify-content: flex-end;
}

.sa-modal-submit {
  min-width: 140px;
}

/* 侧边栏样式 */
.sa-sidebar {
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
  padding: 1.2rem 1.4rem;
  border-bottom: 1px solid var(--sa-border);
}

.sa-sidebar-title {
  font-size: 1rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sa-ink);
  margin: 0;
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

.sa-sidebar-new-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
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


@media (max-width: 1024px) {
  .sa-main-wrapper {
    flex-direction: column;
    padding: 0 1.5rem;
  }

  .sa-main-wrapper--with-memo {
    justify-content: center;
    padding: 0 1.5rem;
  }

  .sa-chat-shell {
    max-width: 100% !important;
    width: 100% !important;
    flex: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  .sa-main-wrapper--with-memo .sa-chat-shell {
    max-width: 100% !important;
    width: 100% !important;
    flex: none !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  .sa-memo-panel {
    flex: 0 0 auto !important;
    width: 100% !important;
    max-width: 100% !important;
    position: relative;
    top: 0;
    max-height: calc(100vh - 4rem); /* 平板端也使用相同的高度限制 */
    margin-top: 1.5rem;
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
}

@media (max-width: 768px) {
  .sa-sidebar {
    width: 280px;
  }

  .sa-sidebar-toggle-btn {
    top: 1rem;
    left: 1rem;
    padding: 0.5rem;
  }

  .sa-chat-root {
    padding: 1.5rem 0;
  }

  .sa-main-wrapper {
    padding: 0 1rem;
    gap: 1.5rem;
  }

  .sa-chat-shell {
    padding: 1.6rem 1.4rem 1.4rem;
  }

  .sa-memo-panel {
    padding: 1.6rem 1.4rem 1.4rem;
    max-height: calc(100vh - 4rem); /* 移动端也使用相同的高度限制 */
  }

  .sa-modal {
    padding: 1.5rem;
  }

  .sa-chat-title-block {
    width: 100%;
  }
}

/* 黑夜模式样式 */
:global(.dark) .sa-chat-root {
  background: var(--sa-bg);
}

:global(.dark) .sa-chat-shell,
:global(.dark) .sa-memo-panel,
:global(.dark) .sa-modal {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

:global(.dark) .sa-chat-paper {
  background: #4a4a4a !important; /* 深灰色背景，确保白色文字清晰可见 */
  border-color: var(--sa-border);
}

:global(.dark) .sa-memo-panel {
  background: #4a4a4a !important; /* 深灰色背景，确保白色文字清晰可见 */
}

:global(.dark) .sa-chat-input-row {
  background: #4a4a4a !important; /* 输入框容器深灰色背景 */
  border-color: var(--sa-border);
}

:global(.dark) .sa-chat-input {
  background: transparent !important; /* 输入框背景透明，使用容器的深灰色 */
  color: #f5f1ea !important; /* 白色文字，在深灰色背景上清晰可见 */
  border-color: var(--sa-border);
}

:global(.dark) .sa-chat-input:focus {
  background: transparent !important;
  border-color: rgba(163, 177, 138, 0.6);
  color: #f5f1ea !important; /* 聚焦时也保持白色 */
}

:global(.dark) .sa-chat-input::placeholder {
  color: rgba(245, 241, 234, 0.6) !important; /* 占位符使用浅白色，在深灰色背景上可见 */
}

:global(.dark) .sa-modal-overlay {
  background: rgba(0, 0, 0, 0.7);
}

:global(.dark) .sa-modal-input {
  background: rgba(40, 40, 38, 0.9);
  color: #3f3c37 !important; /* 模态框输入框文字保持深色 */
  border-color: var(--sa-border);
}

:global(.dark) .sa-modal-input:focus {
  background: rgba(45, 45, 43, 0.95);
  border-color: rgba(163, 177, 138, 0.6);
  color: #3f3c37 !important; /* 聚焦时也保持深色 */
}

:global(.dark) .sa-sidebar {
  background: var(--sa-card-glass);
  border-color: var(--sa-border);
}

:global(.dark) .sa-sidebar-overlay {
  background: rgba(0, 0, 0, 0.5);
}

/* 深色模式下，对话框、输入框和手札的背景改为深灰色，文字改为白色 */
/* 使用 !important 覆盖全局样式，确保在深灰色背景上白色文字清晰可见 */

/* 对话框内容文字 - 白色 */
:global(.dark) .sa-chat-entry-text,
:global(.dark) .sa-chat-entry-text *,
:global(.dark) .sa-chat-entry-text :deep(*),
:global(.dark) .sa-chat-entry-text :deep(p),
:global(.dark) .sa-chat-entry-text :deep(span),
:global(.dark) .sa-chat-entry-text :deep(div),
:global(.dark) .sa-chat-entry-text :deep(strong),
:global(.dark) .sa-chat-entry-text :deep(em),
:global(.dark) .sa-chat-entry-text :deep(a),
:global(.dark) .sa-chat-entry-text :deep(li),
:global(.dark) .sa-chat-entry-text :deep(ul),
:global(.dark) .sa-chat-entry-text :deep(ol),
:global(.dark) .sa-chat-entry-text :deep(h1),
:global(.dark) .sa-chat-entry-text :deep(h2),
:global(.dark) .sa-chat-entry-text :deep(h3),
:global(.dark) .sa-chat-entry-text :deep(h4),
:global(.dark) .sa-chat-entry-text :deep(h5),
:global(.dark) .sa-chat-entry-text :deep(h6) {
  color: #f5f1ea !important; /* 白色文字，在深灰色背景上清晰可见 */
}

/* Distill Visuals 按钮 - 黑夜模式 */
:global(.dark) .sa-chat-distill-btn {
  border-color: rgba(163, 177, 138, 0.5);
  color: #f5f1ea;
}

:global(.dark) .sa-chat-distill-btn:hover {
  background: rgba(163, 177, 138, 0.2);
  border-color: rgba(163, 177, 138, 0.8);
  color: #f5f1ea;
}

/* 手札内容文字 - 白色 */
:global(.dark) .sa-memo-text,
:global(.dark) .sa-memo-text *,
:global(.dark) .sa-memo-text :deep(*),
:global(.dark) .sa-memo-text :deep(p),
:global(.dark) .sa-memo-text :deep(span),
:global(.dark) .sa-memo-text :deep(div),
:global(.dark) .sa-memo-text :deep(strong),
:global(.dark) .sa-memo-text :deep(em),
:global(.dark) .sa-memo-text :deep(a),
:global(.dark) .sa-memo-text :deep(li),
:global(.dark) .sa-memo-text :deep(ul),
:global(.dark) .sa-memo-text :deep(ol),
:global(.dark) .sa-memo-text :deep(h1),
:global(.dark) .sa-memo-text :deep(h2),
:global(.dark) .sa-memo-text :deep(h3),
:global(.dark) .sa-memo-text :deep(h4),
:global(.dark) .sa-memo-text :deep(h5),
:global(.dark) .sa-memo-text :deep(h6) {
  color: #f5f1ea !important; /* 白色文字，在深灰色背景上清晰可见 */
}

:global(.dark) .sa-chat-placeholder {
  color: rgba(130, 126, 118, 0.7) !important; /* 占位符文字使用灰色 */
}

/* 模态框中的文字也保持深色 */
:global(.dark) .sa-modal-intro,
:global(.dark) .sa-modal-intro *,
:global(.dark) .sa-modal-intro :deep(*),
:global(.dark) .sa-modal-title,
:global(.dark) .sa-modal-label {
  color: #3f3c37 !important;
}

:global(.dark) .sa-modal-intro :deep(strong) {
  color: #3f3c37 !important;
}
</style>



