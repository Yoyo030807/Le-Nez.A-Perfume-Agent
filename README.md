# Scent Alchemist | 气味炼金术士

> A minimalist, high-end scent & tech journal.  playable website: https://scentalchemist.netlify.app/
> 极简高端的气味与技术手记。游玩网址：https://scentalchemist.netlify.app/ （电脑端可以，移动端排版还没修正）

---

## ✨ 项目简介

**Scent Alchemist** 是一个融合了香气、情绪与技术的全栈 Web 应用。通过 AI 驱动的对话、智能成分分析和创意设计工具，为用户提供个性化的嗅觉体验。

### 核心功能

#### 🏛️ The Salon · 沙龙会客
与 **Le Nez** 先生对话，通过三阶段情感疗愈流程，定制你的嗅觉记忆。

- **情感探索**：深入挖掘用户故事与情绪
- **香型发现**：了解日常生活中的嗅觉偏好
- **方案定制**：提供概念配方或真实香水推荐

#### 🎨 The Atelier · 香水画室
将无形的香气凝结为有形的设计。

- 可视化香水配方创建
- 香水瓶设计绘制
- 配方管理与导出

#### 🧪 The Lab · 成分实验室
解析香水成分与安全数据，使用 **RAG (Retrieval-Augmented Generation)** 技术。

- **智能别名解析**：自动识别中文译名、昵称
- **全网搜索**：基于 Tavily 的实时数据检索
- **成分分析**：香调雷达图、前中后调、致敏源检测
- **参考信源**：提供原始数据来源链接

---

## 🛠️ 技术栈

### 前端
- **VitePress** - 静态站点生成器
- **Vue 3** (Composition API) - 响应式框架
- **Chart.js** - 数据可视化（雷达图）
- **TypeScript** - 类型安全

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **DeepSeek LLM** - 大语言模型（支持 OpenAI 兼容 API）
- **Tavily Search** - 实时网络搜索
- **Pydantic** - 数据验证

### RAG 流程
1. **智能别名解析**：LLM 将用户输入转换为官方香水名称
2. **全网搜索**：Tavily 搜索英文资料（Fragrantica、Parfumo、Basenotes 等）
3. **智能验证**：LLM 提取数据并翻译回中文

---

## 📁 项目结构

```
LeNez_v2/
├── backend/
│   ├── server.py              # FastAPI 主服务
│   ├── requirements.txt       # Python 依赖
│   ├── conversations/         # 对话记录存储
│   └── recipes/               # 配方存储
│
├── frontend/
│   ├── docs/
│   │   ├── index.md           # 首页
│   │   ├── chat.md            # The Salon
│   │   ├── atelier.md         # The Atelier
│   │   ├── lab.md             # The Lab
│   │   └── .vitepress/
│   │       ├── config.mts     # VitePress 配置
│   │       └── theme/
│   │           ├── index.ts   # 主题入口
│   │           ├── Layout.vue # 布局组件（含页脚）
│   │           ├── styles.css # 全局样式
│   │           └── components/
│   │               ├── PerfumeChat.vue  # 聊天组件
│   │               ├── Atelier.vue     # 画室组件
│   │               ├── Lab.vue         # 实验室组件
│   │               └── LandingPage.vue # 首页组件
│   └── package.json
│
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- **Python** 3.11+
- **Node.js** 18+
- **npm** 或 **yarn**

### 后端设置

#### 1. 创建虚拟环境

```bash
cd backend
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

在 `backend` 目录下创建 `.env` 文件：

```env
# LLM 配置（DeepSeek 或 OpenAI 兼容 API）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_ID=deepseek-v3.2

# Tavily 搜索 API（可选，用于 The Lab）
TAVILY_API_KEY=your_tavily_api_key_here
```

#### 4. 启动后端服务

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

后端服务运行在：`http://localhost:8001`

### 前端设置

#### 1. 安装依赖

```bash
cd frontend
npm install
```

#### 2. 启动开发服务器

```bash
npm run docs:dev
```

前端服务运行在：`http://localhost:5174`

#### 3. 构建生产版本

```bash
npm run docs:build
npm run docs:preview
```

---

## 📡 API 文档

### 核心接口

#### `POST /api/chat`
与 Le Nez 先生对话。

**请求体：**
```json
{
  "messages": [
    { "role": "user", "content": "我今天心情不太好" }
  ],
  "locale": "zh",
  "conversation_id": "optional_conversation_id",
  "user_name": "optional_user_name"
}
```

**响应：** 流式返回对话内容

---

#### `POST /api/analyze_scent`
分析香水成分（RAG 流程）。

**请求体：**
```json
{
  "name": "路易威登 雷暴"
}
```

**响应：**
```json
{
  "found": true,
  "brand": "Louis Vuitton",
  "name": "Orage / 雷暴",
  "radar_data": {
    "Floral": 3,
    "Woody": 7,
    "Fresh": 8,
    "Spicy": 2,
    "Sweet": 1,
    "Oriental": 4
  },
  "notes": {
    "top": "佛手柑、黑醋栗",
    "middle": "鸢尾、茉莉",
    "base": "雪松、白麝香"
  },
  "allergens": ["Limonene", "Linalool"],
  "longevity": "持久 8h+",
  "safety_brief": "安全简评",
  "reference_urls": ["https://..."]
}
```

---

#### `POST /api/create_recipe`
创建香水配方。

**请求体：**
```json
{
  "name": "配方名称",
  "description": "配方描述",
  "notes": {
    "top": ["前调1", "前调2"],
    "middle": ["中调1", "中调2"],
    "base": ["后调1", "后调2"]
  }
}
```

---

#### `POST /api/draw_bottle`
绘制香水瓶设计。

**请求体：**
```json
{
  "prompt": "描述香水瓶的设计",
  "style": "modern"
}
```

---

### 其他接口

- `GET /api/health` - 健康检查
- `GET /api/conversations` - 获取对话列表
- `GET /api/conversations/{id}` - 获取特定对话
- `GET /api/recipes` - 获取配方列表
- `GET /api/recipes/{id}` - 获取特定配方
- `POST /api/extract_recipe` - 从对话中提取配方

---

## 🎨 设计理念

### 视觉风格
- **极简主义**：大量留白，克制而优雅
- **柔和色调**：米白色背景、鼠尾草绿、烟熏玫瑰
- **玻璃态设计**：毛玻璃效果（backdrop-filter）
- **等宽字体**：技术感与艺术感的平衡

### 交互设计
- **渐进式对话**：三阶段情感疗愈流程
- **实时反馈**：流式响应，即时显示
- **历史记录**：本地存储对话与配方
- **响应式布局**：适配桌面与移动端

---

## 🔧 开发说明

### 前端开发

组件位于 `frontend/docs/.vitepress/theme/components/`：

- **PerfumeChat.vue** - 聊天界面，支持流式响应
- **Atelier.vue** - 配方创建与可视化
- **Lab.vue** - 成分分析，集成 Chart.js 雷达图
- **LandingPage.vue** - 首页导航卡片

### 后端开发

主要文件：`backend/server.py`

- **RAG 流程**：`get_official_name()` → Tavily 搜索 → LLM 验证
- **对话管理**：本地 JSON 文件存储
- **流式响应**：使用 FastAPI `StreamingResponse`

---

## 📝 环境变量说明

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | LLM API 密钥 | ✅ |
| `OPENAI_BASE_URL` | LLM API 基础 URL | ✅ |
| `LLM_MODEL_ID` | 模型 ID（默认：deepseek-v3.2） | ❌ |
| `TAVILY_API_KEY` | Tavily 搜索 API 密钥 | ❌（The Lab 功能需要） |

---

## 🐛 故障排除

### 后端启动失败
- 检查 `.env` 文件是否存在且配置正确
- 确认虚拟环境已激活
- 检查端口 8001 是否被占用

### 前端无法连接后端
- 确认后端服务已启动
- 检查 `frontend/docs/.vitepress/theme/components/` 中的 API 地址
- 确认 CORS 配置正确

### The Lab 搜索失败
- 检查 `TAVILY_API_KEY` 是否配置
- 确认网络连接正常
- 查看后端日志了解详细错误

---

## 📄 许可证

MIT License

Copyright (c) 2025 Yaoyao YU

---

## 👤 作者

**Yaoyao YU**

- GitHub: [@Yoyo030807](https://github.com/Yoyo030807)
- 项目地址: [Le-Nez.A-Perfume-Agent](https://github.com/Yoyo030807/Le-Nez.A-Perfume-Agent)

---

## 🙏 致谢

- **VitePress** - 优秀的静态站点生成器
- **FastAPI** - 现代化的 Python Web 框架
- **DeepSeek** - 强大的大语言模型
- **Tavily** - 实时网络搜索服务

---

**Designed & Coded with ❤️ by Yaoyao YU © 2025**
