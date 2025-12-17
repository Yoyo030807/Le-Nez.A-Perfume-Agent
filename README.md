Scent Alchemist · 气味炼金术士
================================

一个围绕香气、情绪与技术的极简高雅博客实验项目。

本项目包含：

- 前端：基于 **VitePress** 的技术博客站点，内置自定义聊天组件 `PerfumeChat`。
- 后端：基于 **FastAPI** 的轻量 API 服务，提供 `/api/chat` 接口，目前为 **Mock 阶段**，返回随机优雅文案。

---

项目结构
--------

```text
LeNez/
  README.md
  backend/
    server.py
    requirements.txt
    .env.example
  frontend/
    package.json
    docs/
      index.md
      .vitepress/
        config.mts
        theme/
          index.ts
          styles.css
          components/
            PerfumeChat.vue
```

---

后端：FastAPI 服务
------------------

### 1. 创建虚拟环境并安装依赖

```bash
cd /Users/yuyongquanjiashi/LeNez/backend

# 创建虚拟环境（示例使用 venv）
python3 -m venv .venv

# 激活虚拟环境（macOS / Linux）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend` 目录下创建 `.env` 文件（可参考 `.env.example`）：

```bash
cd /Users/yuyongquanjiashi/LeNez/backend
cp .env.example .env
```

目前只是从 `.env` 中读取 `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`，但 **Mock 阶段暂时不会真正调用 LLM**。

### 3. 启动后端服务

```bash
cd /Users/yuyongquanjiashi/LeNez/backend
source .venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

后端地址默认为：`http://localhost:8000`

---

前端：VitePress 博客
--------------------

### 1. 安装依赖

```bash
cd /Users/yuyongquanjiashi/LeNez/frontend
npm install
```

### 2. 启动开发服务器

```bash
cd /Users/yuyongquanjiashi/LeNez/frontend
npm run docs:dev
```

默认访问地址：`http://localhost:5173`

---

前后端联调说明
--------------

- 前端的 `PerfumeChat` 组件会向 `http://localhost:8000/api/chat` 发送 `POST` 请求（JSON 格式）。
- FastAPI 后端会返回一条随机的优雅文案，例如：

  > 我闻到了雨后泥土的气息，像是记忆里一封未寄出的信。

这可以帮助你先验证「从 Markdown 中嵌入聊天组件 → 调用后端 API → 将回复展示在聊天窗口」这一完整链路。

当你准备好接入真正的 LLM 时，可以在 `server.py` 中替换 Mock 回复逻辑，并使用 `.env` 中的 `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`。



