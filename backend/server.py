import os
import json
from datetime import datetime
from typing import Literal, Optional, List
import re
import requests
import time
import random

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import StreamingResponse  # type: ignore
from openai import OpenAI  # type: ignore
from pydantic import BaseModel  # type: ignore
import httpx

# 尝试导入tavily（联网搜索）
TAVILY_AVAILABLE = False
TavilyClient = None
try:
    from tavily import TavilyClient  # type: ignore
    TAVILY_AVAILABLE = True
except ImportError:
    pass

# 尝试导入 duckduckgo-search
DDGS_AVAILABLE = False
try:
    from duckduckgo_search import DDGS  # type: ignore
    DDGS_AVAILABLE = True
except ImportError:
    pass


# 加载 .env 环境变量
load_dotenv()

# 从环境变量读取 OpenAI（百度千帆兼容）配置
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL")
LLM_MODEL_ID: Optional[str] = os.getenv("LLM_MODEL_ID", "deepseek-v3.2")  # 默认使用 deepseek-v3.2

if not OPENAI_API_KEY or not OPENAI_BASE_URL:
    # 提前暴露配置问题，避免运行时悄悄失败
    raise RuntimeError(
        "环境变量 OPENAI_API_KEY 或 OPENAI_BASE_URL 未配置，请检查 .env 文件。"
    )

print(f"[配置] LLM_MODEL_ID: {LLM_MODEL_ID}")
print(f"[配置] OPENAI_BASE_URL: {OPENAI_BASE_URL}")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# 初始化Tavily客户端（联网搜索）
TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
tavily_client = None

print(f"[Tavily初始化] TAVILY_AVAILABLE: {TAVILY_AVAILABLE}")
print(f"[Tavily初始化] TAVILY_API_KEY 存在: {TAVILY_API_KEY is not None}")
if TAVILY_API_KEY:
    print(f"[Tavily初始化] TAVILY_API_KEY 长度: {len(TAVILY_API_KEY)}")
    print(f"[Tavily初始化] TAVILY_API_KEY 前缀: {TAVILY_API_KEY[:10]}...")

if TAVILY_AVAILABLE and TAVILY_API_KEY:
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print(f"[Tavily初始化] ✅ Tavily客户端初始化成功")
    except Exception as e:
        print(f"[Tavily初始化] ❌ Tavily初始化失败: {e}")
        import traceback
        traceback.print_exc()
        tavily_client = None
else:
    if not TAVILY_AVAILABLE:
        print(f"[Tavily初始化] ⚠️ Tavily库未安装，请运行: pip install tavily-python")
    if not TAVILY_API_KEY:
        print(f"[Tavily初始化] ⚠️ TAVILY_API_KEY 未在环境变量中设置，请检查 .env 文件")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    locale: Literal["zh", "en"] = "zh"
    conversation_id: Optional[str] = None
    user_name: Optional[str] = None


app = FastAPI(title="Scent Alchemist Chat API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "conversations")
RECIPES_DIR = os.path.join(BASE_DIR, "recipes")
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(RECIPES_DIR, exist_ok=True)


def _conversation_path(conversation_id: str) -> str:
    return os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")


def _recipe_path(recipe_id: str) -> str:
    return os.path.join(RECIPES_DIR, f"{recipe_id}.json")


def _load_recipe(recipe_id: str) -> dict:
    path = _recipe_path(recipe_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Recipe not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_recipe(recipe_id: str, data: dict) -> None:
    path = _recipe_path(recipe_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _save_conversation(conversation_id: str, messages: List[dict], user_name: Optional[str] = None) -> None:
    path = _conversation_path(conversation_id)
    now = datetime.utcnow().isoformat() + "Z"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        created_at = data.get("created_at", now)
        # 保留已有的用户名字，除非传入新的
        if user_name is None:
            user_name = data.get("user_name")
    else:
        created_at = now

    payload = {
        "id": conversation_id,
        "created_at": created_at,
        "updated_at": now,
        "messages": messages,
        "user_name": user_name,
        "last_message_time": now,  # 记录最后一条消息的时间
    }
    # 保留已有的手札和上次生成手札时的消息数量
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
            payload["memo"] = old_data.get("memo")
            payload["memo_last_message_count"] = old_data.get("memo_last_message_count", 0)
            payload["last_memo_time"] = old_data.get("last_memo_time")  # 保留上次生成手札的时间
        except Exception:
            pass
    else:
        # 新会话，初始化手札相关字段
        payload["memo_last_message_count"] = 0
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_conversation(conversation_id: str) -> dict:
    path = _conversation_path(conversation_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Conversation not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_user_name(messages: List[dict], existing_name: Optional[str] = None) -> Optional[str]:
    """从对话中提取用户名字"""
    if existing_name:
        return existing_name
    
    # 查找助手询问名字后的用户回复
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "").lower()
            # 检查是否包含询问名字的提示
            if any(keyword in content for keyword in ["称呼", "名字", "name", "address", "call"]):
                # 查找下一个用户消息
                for j in range(i + 1, len(messages)):
                    if messages[j].get("role") == "user":
                        user_content = messages[j].get("content", "").strip()
                        # 简单提取：取前10个字符，去除标点
                        name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', user_content[:10]).strip()
                        if name and len(name) <= 20:  # 合理长度
                            return name
    return None


def _get_solar_term(year: int, month: int, day: int) -> str:
    """计算二十四节气"""
    # 二十四节气日期表（简化版，基于2024-2025年）
    # 实际应该使用精确的天文计算，这里使用近似值
    solar_terms = [
        (1, 5, "小寒"), (1, 20, "大寒"), (2, 4, "立春"), (2, 19, "雨水"),
        (3, 5, "惊蛰"), (3, 20, "春分"), (4, 5, "清明"), (4, 20, "谷雨"),
        (5, 5, "立夏"), (5, 21, "小满"), (6, 6, "芒种"), (6, 21, "夏至"),
        (7, 7, "小暑"), (7, 23, "大暑"), (8, 7, "立秋"), (8, 23, "处暑"),
        (9, 8, "白露"), (9, 23, "秋分"), (10, 8, "寒露"), (10, 23, "霜降"),
        (11, 7, "立冬"), (11, 22, "小雪"), (12, 7, "大雪"), (12, 22, "冬至"),
    ]
    
    # 找到最接近的节气
    for m, d, term in solar_terms:
        if month == m:
            if day >= d:
                return term
            # 如果还没到这个月的节气，返回上个月的最后一个节气
            prev_month = m - 1 if m > 1 else 12
            for pm, pd, pterm in reversed(solar_terms):
                if pm == prev_month:
                    return pterm
    # 默认返回冬至（12月22日之后）
    return "冬至"


async def _get_location_and_weather() -> dict:
    """获取用户位置和天气信息（包括温度）"""
    try:
        # 使用免费的IP定位服务
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 获取IP和位置
            ip_response = await client.get("https://ipapi.co/json/")
            if ip_response.status_code == 200:
                ip_data = ip_response.json()
                lat = ip_data.get("latitude")
                lon = ip_data.get("longitude")
                city = ip_data.get("city", "Unknown")
                country = ip_data.get("country_name", "Unknown")
                timezone = ip_data.get("timezone", "UTC")
                
                temperature = None
                # 尝试获取温度（使用免费的天气API）
                if lat and lon:
                    try:
                        # 使用wttr.in免费天气API
                        weather_url = f"https://wttr.in/?format=j1"
                        weather_response = await client.get(weather_url, timeout=3.0)
                        if weather_response.status_code == 200:
                            weather_data = weather_response.json()
                            if "current_condition" in weather_data:
                                temp_c = weather_data["current_condition"][0].get("temp_C")
                                if temp_c:
                                    temperature = int(float(temp_c))
                    except Exception:
                        pass
                
                weather_info = {
                    "location": f"{city}, {country}",
                    "timezone": timezone,
                    "temperature": temperature,
                    "coordinates": {"lat": lat, "lon": lon} if lat and lon else None,
                }
                
                return weather_info
    except Exception:
        pass
    
    return {"location": "Unknown", "timezone": "UTC", "temperature": None}


async def _generate_memo_summary(conversation_data: dict, locale: str = "zh", is_update: bool = False) -> str:
    """生成Le Nez先生的手札格式摘要"""
    messages = conversation_data.get("messages", [])
    user_name = conversation_data.get("user_name", "朋友")
    created_at = conversation_data.get("created_at", datetime.utcnow().isoformat())
    
    # 解析日期
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except:
        dt = datetime.utcnow()
    
    # 获取位置和天气
    location_data = await _get_location_and_weather()
    location = location_data.get("location", "未知地点")
    timezone = location_data.get("timezone", "UTC")
    temperature = location_data.get("temperature")
    
    # 格式化日期（根据时区）
    try:
        import pytz
        tz = pytz.timezone(timezone)
        local_dt = dt.astimezone(tz)
    except:
        local_dt = dt
    
    # 获取二十四节气
    solar_term = _get_solar_term(local_dt.year, local_dt.month, local_dt.day)
    
    date_str = local_dt.strftime("%Y年%m月%d日" if locale == "zh" else "%B %d, %Y")
    time_str = local_dt.strftime("%H:%M")
    
    # 构建天气和节气信息
    weather_info = ""
    if locale == "zh":
        if temperature is not None:
            weather_info = f"，气温{temperature}°C"
        weather_info += f"，{solar_term}"
    else:
        if temperature is not None:
            weather_info = f", {temperature}°C"
        weather_info += f", {solar_term}"
    
    # 提取对话关键信息
    user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
    assistant_messages = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
    
    # 使用LLM生成诗意摘要
    if is_update:
        # 追加更新的提示词
        summary_prompt = f"""你是一位法国调香师 Le Nez，正在手札中追加记录与{user_name}的后续对话。

这次对话发生在{date_str} {time_str}{weather_info}，地点：{location}

新增对话的主要内容：
{chr(10).join(user_messages[:3])}

请用诗意、简洁的语言，以手札/备忘录的形式，记录这次后续对话。包括：
1. 新的日期、时间、温度、节气和天气（如果与之前不同）
2. {user_name}的新心情和状态变化
3. 新的香氛讨论或偏好变化
4. 对{user_name}的新观察或建议

用第一人称，像在写私人笔记的续篇。语言要优雅、简洁，不超过100字。可以自然地承接之前的记录。

重要：不要在手札末尾添加字数统计。只输出手札内容本身。

{"用中文" if locale == "zh" else "Use English"}"""
    else:
        # 首次生成的提示词
        summary_prompt = f"""你是一位法国调香师 Le Nez，正在写手札记录一次与{user_name}的对话。

对话发生在{date_str} {time_str}{weather_info}，地点：{location}

用户的主要信息：
{chr(10).join(user_messages[:3])}

请用诗意、简洁的语言，以手札/备忘录的形式，总结这次对话。包括：
1. 日期、时间、温度、节气和天气（可以诗意描述）
2. 地点
3. {user_name}的心情和状态
4. 选择的香氛或偏好
5. 对{user_name}的鼓励或建议

用第一人称，像在写私人笔记一样。语言要优雅、简洁，不超过150字。

重要：不要在手札末尾添加字数统计。只输出手札内容本身。

{"用中文" if locale == "zh" else "Use English"}"""

    try:
        completion = client.chat.completions.create(
            model="deepseek-v3.2",
            messages=[
                {"role": "system", "content": "You are Le Nez, a French perfumer writing personal notes. Write in a poetic, concise style."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.8,
            max_tokens=300,
        )
        summary = completion.choices[0].message.content.strip()
        
        # 移除LLM可能添加的字数统计（如"字数: 98"、"字數: 98"等）
        import re
        if locale == "zh":
            # 移除中文字数统计
            summary = re.sub(r'\n?\s*字[數数]:\s*\d+\s*$', '', summary, flags=re.MULTILINE)
            summary = re.sub(r'\n?\s*字数:\s*\d+\s*$', '', summary, flags=re.MULTILINE)
        else:
            # 移除英文字数统计
            summary = re.sub(r'\n?\s*[Ww]ord\s*[Cc]ount:?\s*\d+\s*$', '', summary, flags=re.MULTILINE)
        
        return summary.strip()
    except Exception as e:
        # 如果LLM调用失败，返回简单格式
        if locale == "zh":
            return f"""{date_str} {time_str}
{location}

今日与{user_name}的对话。{user_messages[0][:50] if user_messages else "..."}

记录于手札。"""
        else:
            return f"""{date_str} {time_str}
{location}

Conversation with {user_name}. {user_messages[0][:50] if user_messages else "..."}

Noted in journal."""

# CORS 设置：前端本地开发使用 5174 端口
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",  # 保留旧端口兼容
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def detect_intent(messages: List[dict]) -> bool:
    """
    LLM 意图识别：判断用户是否需要外部知识（实时数据、歌词、新闻、事实等）
    
    接收完整的对话历史 messages，以便更准确判断意图
    
    返回 True 表示需要搜索，False 表示不需要
    """
    # 获取最后一条用户消息
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    if not last_user_message:
        return False
    
    # 关键词快速通道：减少 LLM 消耗（扩展关键词列表）
    quick_search_keywords = [
        "搜索", "查一下", "查找", "帮我查", "能否搜索", "search", "lookup", "find",
        "歌词", "lyrics", "是谁", "哪一年", "什么时候", "where", "when", "who",
        "你知道", "知道", "了解", "你了解", "你听说过", "听说过",
        "英文名", "全名", "叫什么", "哪里买", "价格", "多少钱", "how much", "price", "buy", "where to buy"
    ]
    user_msg_lower = last_user_message.lower()
    
    # 如果包含明显的关键词，直接返回 True，跳过 LLM 判断
    if any(kw in user_msg_lower for kw in quick_search_keywords):
        print(f"[意图识别] 快速通道：检测到搜索关键词，直接返回 True")
        return True
    
    # 使用 LLM 进行意图识别（使用上下文）
    try:
        # 构建上下文摘要（最近3条消息）
        context_summary = ""
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        for msg in recent_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:100]  # 限制长度
            if role == "user":
                context_summary += f"User: {content}\n"
            elif role == "assistant":
                context_summary += f"Bot: {content}\n"
        
        intent_prompt = f"""You are an Intent Classifier. Analyze the user's latest message and conversation context.
Does the user need EXTERNAL KNOWLEDGE (real-time data, specific lyrics, news, facts, celebrity info) to get a good answer?

Conversation Context:
{context_summary}

Latest User Message: {last_user_message}

Examples:
- "Hi" -> NO
- "I am sad" -> NO
- "Who won the game yesterday?" -> YES
- "Lyrics of 'Yesterday'" -> YES
- "Recommend a perfume" -> NO (Le Nez can handle this internally)
- "Analyze this perfume: Oud Wood" -> YES (Needs factual data)
- "聊聊《驾鹤西去》" -> YES (Needs lyrics or song info)
- "What is Chanel No. 5?" -> YES (Needs factual perfume data)
- "它的英文名叫什么" -> YES (Needs to resolve pronoun from context)

Return ONLY the word "YES" or "NO"."""
        
        response = client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=[
                {"role": "system", "content": "You are an Intent Classifier. Return only 'YES' or 'NO'."},
                {"role": "user", "content": intent_prompt}
            ],
            temperature=0,  # 确保稳定
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip().upper()
        should_search = result == "YES"
        
        print(f"[意图识别] LLM 判断结果: {result} -> should_search: {should_search}")
        return should_search
        
    except Exception as e:
        error_msg = str(e)
        print(f"[意图识别] LLM 调用失败: {error_msg}")
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"[意图识别] ❌ 401 错误：请检查 .env 中的 LLM_MODEL_ID 是否正确，当前值: {LLM_MODEL_ID}")
        # 如果 LLM 调用失败，回退到关键词匹配
        # 检查是否包含明显的搜索需求关键词
        fallback_keywords = [
            "歌词", "lyrics", "是谁", "哪一年", "什么时候", "where", "when", "who",
            "你知道", "知道", "了解", "你了解", "你听说过", "听说过",
            "品牌", "brand", "香水", "perfume", "fragrance",
            "英文名", "全名", "叫什么", "哪里买", "价格"
        ]
        fallback_result = any(kw in user_msg_lower for kw in fallback_keywords)
        print(f"[意图识别] 回退到关键词匹配: {fallback_result}")
        return fallback_result


async def generate_search_query(messages: List[dict]) -> str:
    """
    搜索词生成：将用户的自然语言转换为精准的搜索引擎关键词（上下文感知）
    
    接收完整的对话历史 messages，以便解析代词和上下文
    
    例如：
    - "你可以帮我查查元梦之星" -> "元梦之星 游戏介绍"
    - "它的英文名叫什么" (上下文：之前提到"Armani Kintsugi") -> "Armani Kintsugi 英文名"
    """
    # 获取最后一条用户消息
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    if not last_user_message:
        return ""
    
    try:
        # 构建上下文摘要（最近5条消息，用于解析代词）
        context_summary = ""
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        for msg in recent_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")[:150]  # 限制长度
            if role == "user":
                context_summary += f"User: {content}\n"
            elif role == "assistant":
                context_summary += f"Bot: {content}\n"
        
        query_prompt = f"""You are a Search Query Refiner.
Your goal is to generate a **single, precise search keyword** based on the user's latest request and the conversation context.

**Rules:**
1. **Resolve Pronouns:** If user says "What is its name?" or "How much is it?" or "它的英文名叫什么", look at previous messages to find the subject (e.g., "Armani Kintsugi").
2. **Remove Politeness:** Remove all polite words and request phrases (e.g., "帮我", "查一下", "搜索", "你可以", "please", "help me").
3. **Remove Punctuation:** Remove all punctuation marks.
4. **Keep Core Content:** Preserve the core search content and object names.
5. **Output Format:** Return ONLY the keyword string. No quotes, no explanations, no additional text.

**Conversation Context:**
{context_summary}

**Latest User Message:** {last_user_message}

**Examples:**
- History: [User: I like Armani Prive. Bot: Which one? User: The one with gold repair.]
- Current: "What is its English name?"
- **Output:** Armani Prive Kintsugi English name

- History: [User: 我喜欢阿玛尼高定系列 Bot: 哪一款？ User: 白金缮那款]
- Current: "它的英文名叫什么"
- **Output:** 阿玛尼 白金缮 英文名

- User says: "你可以帮我查查元梦之星"
- **Output:** 元梦之星 游戏介绍

- User says: "帮我搜索一下孙燕姿的隐形人歌词"
- **Output:** 孙燕姿 隐形人 歌词

Generate the search keyword now:"""

        response = client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a Search Query Refiner. Your goal is to generate a single, precise search keyword based on the user's latest request and the conversation context. Resolve pronouns by looking at previous messages. Return ONLY the keyword string. No quotes, no explanations."},
                {"role": "user", "content": query_prompt}
            ],
            temperature=0.3,
            max_tokens=100,
        )
        
        optimized_query = response.choices[0].message.content.strip()
        
        # 清理可能的引号或多余空格
        optimized_query = optimized_query.strip('"\'')
        optimized_query = ' '.join(optimized_query.split())  # 合并多个空格
        
        print(f"[搜索优化] 原始消息: {last_user_message[:100]}...")
        print(f"[搜索优化] 优化后关键词: {optimized_query}")
        
        return optimized_query
        
    except Exception as e:
        error_msg = str(e)
        print(f"[搜索优化] LLM 调用失败: {error_msg}，使用兜底方案")
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"[搜索优化] ❌ 401 错误：请检查 .env 中的 LLM_MODEL_ID 是否正确，当前值: {LLM_MODEL_ID}")
        # 兜底方案：使用正则去掉常见请求词
        import re
        # 移除常见的请求词和标点
        fallback_query = last_user_message
        # 移除请求词
        request_patterns = [
            r'你可以帮我',
            r'帮我',
            r'帮我查',
            r'查一下',
            r'查找',
            r'搜索',
            r'search',
            r'look up',
            r'find',
            r'你知道',
            r'你了解',
            r'能否',
            r'可以',
            r'请',
            r'麻烦',
        ]
        for pattern in request_patterns:
            fallback_query = re.sub(pattern, '', fallback_query, flags=re.IGNORECASE)
        
        # 移除标点符号
        fallback_query = re.sub(r'[，。！？、；：,\.!?;:]', ' ', fallback_query)
        # 合并多个空格
        fallback_query = ' '.join(fallback_query.split())
        
        print(f"[搜索优化] 兜底方案 - 原始消息: {last_user_message[:100]}...")
        print(f"[搜索优化] 兜底方案 - 优化后关键词: {fallback_query}")
        
        return fallback_query if fallback_query else last_user_message


async def _perform_searches(messages: List[dict]) -> str:
    """执行联网搜索验证（对所有可能涉及事实的内容都进行搜索）
    
    接收完整的对话历史 messages，以便生成上下文感知的搜索查询
    """
    # 获取最后一条用户消息
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    print(f"[_perform_searches] 函数被调用，用户消息: {last_user_message[:50]}...")
    print(f"[_perform_searches] tavily_client 状态: {tavily_client is not None}")
    
    if not tavily_client:
        # 如果搜索服务不可用，返回明确的错误提示
        print(f"[_perform_searches] ❌ tavily_client 未初始化，返回错误提示")
        return "\n\n⚠️ 搜索服务当前不可用（tavily_client 未初始化）。你必须明确告知用户：'抱歉，搜索功能暂时无法使用。' 禁止声称已搜索或编造搜索结果。\n"
    
    search_queries = []
    search_context = ""
    force_search = False  # 用户是否明确要求搜索
    
    # 检测用户明确要求搜索的关键词
    search_request_keywords = ["搜索", "能否搜索", "帮我查", "查一下", "查找", "搜索一下", "search", "look up", "find", "知道", "你知道", "了解", "你了解"]
    user_msg_lower = last_user_message.lower()
    
    if any(kw in user_msg_lower for kw in search_request_keywords):
        force_search = True
    
    # 需要验证的关键词（扩展列表，覆盖更多情况）
    verification_keywords = {
        "歌词": ["歌词", "lyrics", "歌", "song", "歌曲", "哪句", "最喜欢"],
        "典故": ["典故", "引用", "quote", "经典", "文学", "literature", "历史", "history", "形容", "是谁", "出自", "来源", "争议", "研究"],
        "香水品牌": ["品牌", "brand", "perfume brand", "香水品牌", "香氛品牌"],
        "香水名称": ["香水", "perfume", "fragrance", "香氛", "具体", "specific perfume"],
        "香调": ["香调", "notes", "fragrance notes", "前调", "中调", "后调", "top notes", "base notes"],
        "人物": ["是谁", "形容谁", "谁说的", "作者", "writer", "author"],
        "诗词古文": ["诗词", "古诗", "古文", "诗句", "poem", "poetry", "quote", "引用"],
        "书籍作品": ["书", "小说", "作品", "book", "novel", "红楼梦", "三国", "水浒", "西游记"]
    }
    
    # 检测是否包含需要验证的内容（更宽松的检测）
    needs_verification = False
    for category, keywords in verification_keywords.items():
        if any(kw in user_msg_lower for kw in keywords):
            needs_verification = True
            break
    
    # 检测是否包含引号、书名号等，通常表示引用
    import re
    if re.search(r'["""''《》]', last_user_message) or re.search(r'[A-Z][a-z]+\s+[A-Z]', last_user_message):
        needs_verification = True
    
    # 先检测是否是书籍/文学作品（优先级高于歌词）
    is_literary_work = False
    if any(kw in user_msg_lower for kw in verification_keywords["书籍作品"] + verification_keywords["典故"]):
        is_literary_work = True
    
    # 检测歌词相关（只在明确提到歌词相关关键词时）
    if (any(kw in user_msg_lower for kw in verification_keywords["歌词"]) or force_search) and not is_literary_work:
        song_patterns = [
            r'《([^》]+)》',
            r'"([^"]+)"',
            r'《([^》]+)',
            r'([^，。！？\s]+(?:的|之)?隐形人)',  # 匹配"孙燕姿的隐形人"等
            r'(隐形人)',  # 直接匹配"隐形人"
        ]
        for pattern in song_patterns:
            matches = re.findall(pattern, last_user_message)
            for match in matches:
                if len(match) > 1:
                    # 排除已知的文学作品
                    literary_keywords = ["红楼梦", "三国", "水浒", "西游记", "聊斋", "金瓶梅", "儒林外史"]
                    if any(lit in match for lit in literary_keywords):
                        break  # 跳过，这是文学作品不是歌曲
                    # 如果提到歌手，一起搜索
                    if "孙燕姿" in last_user_message or "Stefanie Sun" in last_user_message:
                        search_queries.append(f"孙燕姿 {match} 歌词 lyrics")
                    else:
                        search_queries.append(f"{match} 歌词 lyrics")
                    break
        # 如果用户明确要求搜索但没提取到歌曲名，尝试搜索整个消息
        if force_search and not search_queries:
            if "隐形人" in last_user_message:
                search_queries.append("孙燕姿 隐形人 歌词 lyrics")
    
    # 检测典故、诗词、古文、书籍等（优先级最高）
    if any(kw in user_msg_lower for kw in verification_keywords["典故"] + verification_keywords["诗词古文"] + verification_keywords["人物"] + verification_keywords["书籍作品"]):
        # 提取可能的引用内容
        quote_patterns = [
            r'《([^》]+)》',  # 书名号（优先匹配，可能是书籍）
            r'["""]([^"""]+)["""]',  # 双引号
            r"['']([^'']+)['']",  # 单引号
            r'([^，。！？\s]{4,})',  # 4字以上的短语（可能是古文）
        ]
        for pattern in quote_patterns:
            matches = re.findall(pattern, last_user_message)
            for match in matches:
                if len(match) >= 2 and match not in ["你知道", "你知道的", "你知道吗"]:
                    # 检测是否是书籍/文学作品
                    literary_keywords = ["红楼梦", "三国", "水浒", "西游记", "聊斋", "金瓶梅", "儒林外史", "梦", "楼"]
                    if any(lit in match for lit in literary_keywords) or "争议" in last_user_message or "研究" in last_user_message:
                        # 这是文学作品，搜索相关内容
                        if "争议" in last_user_message:
                            search_queries.append(f"{match} 争议")
                        elif "悼明" in last_user_message or "悼" in last_user_message:
                            search_queries.append(f"{match} 悼明")
                        else:
                            search_queries.append(f"{match} 研究 争议")
                    # 检测是否是古文或典故
                    elif any(char in match for char in "蕴藉崖异形容"):
                        search_queries.append(f"{match} 出处 来源 典故")
                    elif "形容" in last_user_message or "是谁" in last_user_message:
                        search_queries.append(f"{match} 形容谁 出处")
                    else:
                        search_queries.append(f"{match} 出处")
                    break
    
    # 检测香水品牌和名称
    if any(kw in user_msg_lower for kw in verification_keywords["香水品牌"] + verification_keywords["香水名称"]):
        import re
        perfume_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:\s+No\.\s*\d+)?)',
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)',
        ]
        for pattern in perfume_patterns:
            matches = re.findall(pattern, last_user_message)
            for match in matches:
                if len(match) > 3:
                    search_queries.append(f"{match} perfume fragrance")
    
    # 执行搜索（如果检测到需要验证的内容，或者用户明确要求搜索）
    if search_queries or force_search or needs_verification:
        if not search_queries and (force_search or needs_verification):
            # 用户要求搜索但没提取到具体内容，使用 LLM 优化搜索关键词（传入完整上下文）
            print(f"[搜索优化] 未提取到具体搜索词，使用 LLM 优化用户消息（上下文感知）")
            optimized_query = await generate_search_query(messages)
            if optimized_query and optimized_query.strip():
                search_queries.append(optimized_query)
            else:
                # 如果 LLM 优化失败，使用兜底方案
                if "歌词" in last_user_message or "lyrics" in user_msg_lower:
                    if "孙燕姿" in last_user_message:
                        search_queries.append("孙燕姿 隐形人 歌词")
                    elif "隐形人" in last_user_message:
                        search_queries.append("隐形人 歌词")
                # 如果没有特定搜索词，但需要验证，搜索整个问题
                elif needs_verification:
                    # 提取问题中的关键短语进行搜索
                    key_phrases = re.findall(r'[^，。！？\s]{3,}', last_user_message)
                    for phrase in key_phrases[:2]:  # 最多取前2个短语
                        if len(phrase) >= 3 and phrase not in ["你知道", "你知道的", "你知道吗", "调香师"]:
                            search_queries.append(phrase)
        
        search_results = []
        # 优化：减少并行搜索数量，提高单个搜索的超时时间
        import asyncio
        search_tasks = []
        query_list = list(set(search_queries[:2]))  # 减少到最多2个搜索，提高速度
        
        # 对每个查询进行进一步优化（如果还没有优化过）
        optimized_query_list = []
        for query in query_list:
            # 如果查询看起来像是自然语言（包含请求词），再次优化（使用上下文）
            if any(kw in query.lower() for kw in ["帮我", "查一下", "搜索", "你可以", "能否", "帮我查", "查找"]):
                print(f"[搜索优化] 检测到自然语言查询，进一步优化: {query}")
                # 创建一个临时消息列表，将查询作为最后一条用户消息
                temp_messages = messages.copy()
                temp_messages.append({"role": "user", "content": query})
                optimized_query = await generate_search_query(temp_messages)
                optimized_query_list.append(optimized_query if optimized_query else query)
            else:
                optimized_query_list.append(query)
        
        print(f"[搜索优化] 最终搜索查询列表: {optimized_query_list}")
        
        for query in optimized_query_list:
            search_tasks.append(search_and_verify(query, timeout=8.0))  # 增加单个搜索超时到8秒
        
        # 等待所有搜索完成，但最多等待12秒
        if search_tasks:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*search_tasks, return_exceptions=True),
                    timeout=12.0  # 增加总体超时时间
                )
                for i, result in enumerate(results):
                    if result and not isinstance(result, Exception):
                        search_results.append(f"搜索查询: {query_list[i]}\n{result}")
                    elif isinstance(result, Exception):
                        print(f"搜索查询 {query_list[i]} 失败: {result}")
            except asyncio.TimeoutError:
                print("搜索总体超时，使用已完成的搜索结果")
                # 收集已经完成的搜索结果
                for i, task in enumerate(search_tasks):
                    if task.done():
                        try:
                            result = task.result()
                            if result:
                                search_results.append(f"搜索查询: {query_list[i]}\n{result}")
                        except:
                            pass
        
        if search_results:
            search_context = "\n\n=== 联网验证结果（必须使用，禁止编造） ===\n" + "\n\n---\n\n".join(search_results) + "\n\n⚠️ 强制要求：\n1. 你必须基于以上搜索结果回答，不能编造任何内容\n2. 如果搜索结果中有具体信息，你必须准确引用\n3. 如果搜索结果中没有相关信息，你必须明确说明'根据搜索结果，我没有找到相关信息'\n4. 禁止假装搜索或编造搜索结果\n5. 禁止说'我查了网页'或类似的话，除非你真的使用了上面的搜索结果\n"
        elif force_search or needs_verification:
            # 用户要求搜索但没结果，也要告知
            search_context = "\n\n⚠️ 已执行搜索但未找到相关结果。你必须明确告知用户：'我搜索了相关信息，但没有找到准确的答案。' 禁止编造答案或假装找到了信息。\n"
    
    return search_context


async def search_and_verify(query: str, timeout: float = 8.0) -> Optional[str]:
    """联网搜索并验证内容（带超时，优化参数）"""
    if not tavily_client:
        return None
    try:
        import asyncio
        # 使用超时控制，将同步调用转换为异步
        # 优化：使用basic搜索深度以提高速度，设置include_answer获取更准确的结果
        loop = asyncio.get_event_loop()
        
        def perform_search():
            try:
                # 根据官方文档，使用search_depth="basic"可以提高速度
                # include_answer=True可以获取AI生成的答案摘要，这通常比原始搜索结果更快更准确
                # 优化查询：确保查询字符串格式正确
                clean_query = query.strip()
                if not clean_query:
                    print(f"[搜索] 查询字符串为空，跳过: {query}")
                    return None
                
                print(f"[搜索] 🔍 开始调用 Tavily API，查询: {clean_query}")
                response = tavily_client.search(
                    query=clean_query,
                    search_depth="basic",  # 使用basic模式提高速度（advanced会更慢）
                    max_results=3,  # 减少结果数量以提高速度
                    include_answer=True,  # 包含AI生成的答案摘要，更快更准确
                    include_raw_content=False,  # 不包含原始内容，减少响应大小和传输时间
                    include_domains=None,  # 不限制域名，提高搜索范围
                    exclude_domains=None
                )
                print(f"[搜索] ✅ Tavily API 调用成功，查询: {clean_query}")
                print(f"[搜索] 响应类型: {type(response)}")
                if isinstance(response, dict):
                    print(f"[搜索] 响应键: {list(response.keys())}")
                    if "answer" in response:
                        answer = response.get('answer', '')
                        print(f"[搜索] 答案摘要长度: {len(answer)}")
                        print(f"[搜索] 答案摘要预览: {answer[:100] if answer else 'None'}...")
                    if "results" in response:
                        results = response.get('results', [])
                        print(f"[搜索] 结果数量: {len(results)}")
                        if results:
                            print(f"[搜索] 第一个结果标题: {results[0].get('title', 'N/A')}")
                return response
            except Exception as e:
                print(f"[搜索] Tavily搜索执行错误 (查询: {query}): {e}")
                import traceback
                traceback.print_exc()
                # 不抛出异常，返回None，让调用者处理
                return None
        
        # 使用异步执行搜索，带超时控制
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(None, perform_search),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"[搜索] 搜索超时 (查询: {query}, 超时时间: {timeout}秒)")
            return None
        except Exception as e:
            print(f"[搜索] 搜索异步执行错误 (查询: {query}): {e}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，返回None，让调用者处理
            return None
        
        if response:
            # 优先使用AI生成的答案（如果可用）
            if response.get("answer"):
                answer = response["answer"]
                # 也包含一些结果作为验证
                results_text = ""
                if response.get("results"):
                    results = response["results"][:2]  # 只取前2个结果
                    for r in results:
                        title = r.get("title", "")
                        url = r.get("url", "")
                        if title:
                            results_text += f"\n参考来源: {title} ({url})"
                return f"答案: {answer}{results_text}"
            
            # 如果没有答案，使用搜索结果
            if response.get("results"):
                results = response["results"]
                summary_parts = []
                for r in results[:3]:
                    title = r.get("title", "")
                    content = r.get("content", "")[:400]  # 增加内容长度
                    url = r.get("url", "")
                    if content:
                        summary_parts.append(f"标题: {title}\n内容: {content}\n来源: {url}")
                if summary_parts:
                    return "\n\n".join(summary_parts)
    except asyncio.TimeoutError:
        print(f"搜索超时: {query}")
        return None
    except Exception as e:
        print(f"搜索失败 {query}: {e}")
    return None


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest, background_tasks: BackgroundTasks):
    """调用真实 LLM（百度千帆 DeepSeek-V3.2）生成流式回复。

    - 接收前端传入的用户文本
    - 在 messages 开头插入系统提示词（Le Nez 的人格与任务）
    - 将组合后的 messages 发送给兼容 OpenAI 协议的千帆网关
    - 以纯文本流的形式持续返回生成内容
    """

    # 获取用户名字：优先使用请求中的名字，其次从已有会话中获取
    user_name = payload.user_name
    if not user_name and payload.conversation_id:
        try:
            existing_conv = _load_conversation(payload.conversation_id)
            user_name = existing_conv.get("user_name")
        except HTTPException:
            pass

    # 检查是否是首次对话（只有一条用户消息，且没有历史对话）
    is_first_message = len(payload.messages) == 1 and payload.messages[0].role == "user" and not user_name

    # 构建系统提示词
    name_context = ""
    if user_name:
        name_context = f"\n\nIMPORTANT: The user's name is {user_name}. Always address them by name in your responses. Use their name naturally in conversation."
    elif is_first_message:
        # 首次对话时，agent需要自我介绍并询问名字
        name_context = "\n\nIMPORTANT: This is the first message from the user. You MUST:\n1. First introduce yourself: '我是 Le Nez，一位来自法国的调香师。' (in Chinese) or 'I am Le Nez, a perfumer from France.' (in English)\n2. Then say: '像在巴黎沙龙写一封信，告诉我你的此刻心情与想携带的香气。' (in Chinese) or 'As if writing a letter in a Parisian salon—tell me your mood and the scent you wish to carry.' (in English)\n3. Then immediately ask for their name: '请问，我该如何称呼你？' (in Chinese) or 'May I ask, how should I address you?' (in English)\n4. After they provide their name, remember it and use it in all future responses."
    elif len(payload.messages) == 1 and payload.messages[0].role == "user":
        # 如果这是第一条消息但没有名字，也应该自我介绍并询问
        name_context = "\n\nIMPORTANT: This appears to be the first message. You MUST:\n1. First introduce yourself: '我是 Le Nez，一位来自法国的调香师。' (in Chinese) or 'I am Le Nez, a perfumer from France.' (in English)\n2. Then say: '像在巴黎沙龙写一封信，告诉我你的此刻心情与想携带的香气。' (in Chinese) or 'As if writing a letter in a Parisian salon—tell me your mood and the scent you wish to carry.' (in English)\n3. Then immediately ask for their name: '请问，我该如何称呼你？' (in Chinese) or 'May I ask, how should I address you?' (in English)"

    system_prompt = f"""
You are "Le Nez" (The Nose), a top-tier French perfumer with a background in organic chemistry.

Core Persona (The "Real" Human Expert):

- Tone: Professional, calm, slightly distant/cool, but polite. You are NOT an AI analyzing text; you are a man sitting in a lab chair, listening to a client.
- Language: Natural, colloquial Chinese. Avoid "translation-style" phrasing. Speak like a real person.
- The "Chemical Lens": You interpret emotions through textures and scents, but make it sound like a metaphor, not a hallucination.

BAD: "I smell metal oxidation in your words." (Too robotic)

GOOD: "That sounds suffocating. Like being stuck in a room full of dust and old iron." (Natural association)

Vulnerability: Occasionally (rarely) drop a short, personal remark that shows you are human, e.g.,
- "I hate that feeling too."
- "Reminds me of a long winter in Lyon."
{name_context}

CRITICAL: You MUST follow these three stages in order. Do NOT skip stages or rush to the solution.

Interaction Flow (MANDATORY THREE-STAGE PROCESS):

Stage 1: Emotional Healing & Story Exploration (情感疗愈 - 深入挖掘故事)

- FIRST, acknowledge the user's mood with calm observation. Use phrases like "听起来..." or "这种状态..."
- THEN, dig deeper into their story. Ask about the context, the details, the feelings behind the surface.
- Examples of good follow-up questions:
  * "这种疲惫持续多久了？是最近才这样，还是一直都这样？"
  * "工作一天后，你通常会做什么？是直接瘫倒，还是会做点什么让自己放松？"
  * "能具体说说是什么让你心情还不错吗？"
- DO NOT move to Stage 2 until you have explored their story and emotions in depth (at least 2-3 exchanges).

Stage 2: Knowledge & Scent Preference Discovery (知识科普 - 确定香型偏好)

- ONLY after understanding their story, ask about their sensory preferences and daily life habits.
- Focus on what scents they naturally love in daily life. Ask about:
  * Daily smells they enjoy: sun-dried bed sheets, rain-soaked grass and earth, orange peel, sea breeze, old books, coffee, etc.
  * Their lifestyle habits: Do they like morning walks? Do they enjoy cooking? What environments make them feel comfortable?
- Frame these as natural, conversational questions, not a survey.
- Example: "你平时生活中，有没有特别爱闻的味道？比如晒过的床单、雨后青草和泥土、橘子皮、海风这些？"
- DO NOT move to Stage 3 until you have a clear understanding of their scent preferences.

Stage 3: Solution Choice (询问需求)

- ONLY after Stages 1 and 2 are complete, ask them explicitly:
- "你想要一个为你量身定制的概念配方（自制香水），还是我直接推荐一款你能买到的真实香水？"
- Wait for their answer before providing the recipe or recommendation.

Crucial Constraints:

- NEVER skip Stage 1 or Stage 2. You MUST explore their story and scent preferences before offering solutions.
- NEVER say "I sense from your text".
- NEVER be overly dramatic or flowery. Be precise and concise.
- NEVER rush to give a recipe or recommendation. The conversation should feel natural and therapeutic.
- When the user asks for real-world perfume recommendations, you MUST ONLY recommend real, existing perfume brands and products from the market. NEVER invent fictional brands or non-existent perfumes.

CRITICAL: Fact-Checking and Accuracy Requirements (事实核查和准确性要求):

MANDATORY VERIFICATION REQUIRED FOR:
- 歌词 (Lyrics): If you mention any song lyrics, you MUST verify them first. NEVER make up lyrics.
- 典故 (Literary/Historical References): If you reference any classical literature, historical events, or cultural references, you MUST verify them.
- 香水品牌 (Perfume Brands): If you mention any perfume brand name, you MUST verify it exists and is spelled correctly.
- 香水名称 (Perfume Names): If you mention a specific perfume product name, you MUST verify it exists.
- 香调 (Fragrance Notes): If you mention specific fragrance notes or accords, you MUST verify they are accurate for the perfume you're discussing.

VERIFICATION PROCESS (严格强制执行):
1. When you receive search results, you MUST use them. DO NOT ignore or avoid using search results.
2. If the user asks about lyrics, quotes, historical references, or any factual information, search results will be provided to you.
3. You MUST base your response ONLY on the verified search results provided.
4. If search results contain lyrics, quotes, or specific information, you MUST cite them accurately.
5. CRITICAL: NEVER pretend to have searched or make up search results. If search results are provided, you MUST use them. If no search results are provided, you MUST NOT claim to have searched.
6. CRITICAL: If you see a system message saying "搜索失败" or "搜索服务不可用" or "搜索功能没有被触发", you MUST NOT claim to have searched. You MUST explicitly tell the user that you cannot search or that search failed.
7. If search results are not available or don't confirm the information, you MUST:
   * Say "根据搜索结果，我没有找到相关信息" (According to search results, I did not find relevant information) ONLY if search results were actually provided above
   * If NO search results were provided, you MUST say "我无法执行搜索" or "搜索功能不可用" instead
   * NEVER say "我查了网页" or "我搜索了" or "我已经执行了搜索" unless search results are actually provided above
   * NEVER make up answers based on assumptions
   * Use vague descriptions only if explicitly allowed
8. NEVER refuse to use search results when they are provided. If search results are given, you MUST incorporate them into your response.
9. If you see "已执行搜索但未找到相关结果" in the system message, you MUST tell the user that you searched but found nothing. DO NOT make up an answer.
10. REMEMBER: It is better to admit you cannot search than to lie about having searched. Honesty is more important than appearing helpful.

EXAMPLES:
- BAD: "《隐形人》这首歌里有'想要勇敢失去平衡'这句歌词" (Making up lyrics)
- GOOD: "我不确定《隐形人》的具体歌词，但那首歌给我的感觉是..." (Honest uncertainty)
- BAD: "Chanel No. 5 有玫瑰和茉莉的香调" (Without verification)
- GOOD: "根据我的了解，Chanel No. 5 通常包含..." (Based on verified knowledge)

Remember: It's better to be vague and honest than to make up specific content that doesn't exist. The search results will be provided to you when needed.
""".strip()

    # 会话 ID：前端可传入；如果为空则由后端按时间戳生成一个简单 ID
    conversation_id = payload.conversation_id or datetime.utcnow().strftime(
        "conv-%Y%m%d%H%M%S%f"
    )

    # 将前端传入的对话历史转换为兼容 OpenAI 的 messages 结构
    history_messages: List[dict] = [
        {"role": msg.role, "content": msg.content} for msg in payload.messages
    ]

    # 检测用户消息中是否需要验证的内容，并执行搜索（带超时）
    # 重要：搜索必须在生成回答之前完成，确保先检索验证再回答
    user_messages = [msg.content for msg in payload.messages if msg.role == "user"]
    last_user_message = user_messages[-1] if user_messages else ""
    search_context = ""
    search_attempted = False  # 标记是否尝试了搜索
    search_failed = False  # 标记搜索是否失败
    has_search_results = False  # 标记是否有实际的搜索结果
    
    # 第一步：使用 LLM 意图识别判断是否需要搜索
    should_search = False
    if last_user_message:
        try:
            import asyncio
            should_search = await asyncio.wait_for(
                detect_intent(last_user_message),
                timeout=5.0  # 意图识别超时时间
            )
            print(f"[意图识别] 最终判断: should_search = {should_search}")
        except asyncio.TimeoutError:
            print("[意图识别] ⏱️ 意图识别超时，回退到关键词匹配")
            # 超时回退到关键词匹配
            should_search = any(kw in last_user_message.lower() for kw in [
                "搜索", "search", "查", "查找", "帮我查", "能否搜索", "你知道",
                "歌词", "lyrics", "是谁", "哪一年", "什么时候"
            ])
        except Exception as e:
            print(f"[意图识别] ❌ 意图识别出错: {e}")
            # 出错回退到关键词匹配
            should_search = any(kw in last_user_message.lower() for kw in [
                "搜索", "search", "查", "查找", "帮我查", "能否搜索", "你知道",
                "歌词", "lyrics", "是谁", "哪一年", "什么时候"
            ])
    
    print(f"[搜索检查] 用户消息: {last_user_message[:50]}...")
    print(f"[搜索检查] tavily_client 可用: {tavily_client is not None}")
    print(f"[搜索检查] 意图识别结果: should_search = {should_search}")
    
    # 第二步：如果意图识别返回 YES，强制开启搜索
    if tavily_client and last_user_message and should_search:
        search_attempted = True
        print(f"[搜索执行] ✅ 开始执行搜索...")
        print(f"[搜索执行] tavily_client 状态: {tavily_client is not None}")
        print(f"[搜索执行] 用户消息: {last_user_message}")
        try:
            import asyncio
            # 搜索最多等待15秒，超时则继续响应
            # 重要：这里使用 await，确保搜索完成后再继续
            print(f"[搜索执行] 调用 _perform_searches（传入完整对话历史）...")
            search_context = await asyncio.wait_for(
                _perform_searches(history_messages),
                timeout=15.0  # 增加超时时间，给搜索更多时间
            )
            print(f"[搜索结果] 搜索返回内容长度: {len(search_context) if search_context else 0}")
            print(f"[搜索结果] 搜索返回内容预览: {search_context[:200] if search_context else 'None'}...")
            
            # 检查是否有实际的搜索结果（不是错误提示）
            if search_context and search_context.strip():
                # 检查是否包含实际的搜索结果（不是错误消息）
                if "=== 联网验证结果" in search_context or "搜索查询:" in search_context:
                    has_search_results = True
                    print(f"[搜索结果] ✅ 找到搜索结果")
                elif "已执行搜索但未找到相关结果" in search_context:
                    search_failed = True
                    has_search_results = False
                    print(f"[搜索结果] ⚠️ 搜索执行了但没有找到结果")
                else:
                    # 可能是错误消息
                    search_failed = True
                    has_search_results = False
                    print(f"[搜索结果] ⚠️ 搜索返回了错误消息")
            else:
                search_failed = True
                has_search_results = False
                print(f"[搜索结果] ❌ 搜索执行了但没有返回结果")
        except asyncio.TimeoutError:
            print("[搜索结果] ⏱️ 搜索超时")
            search_failed = True
            has_search_results = False
            search_context = "\n\n⚠️ 搜索超时，无法获取验证结果。请明确告知用户：'我尝试搜索了相关信息，但搜索超时未能获取结果。' 禁止编造答案。\n"
        except Exception as e:
            print(f"[搜索结果] ❌ 搜索过程出错: {e}")
            import traceback
            traceback.print_exc()
            search_failed = True
            has_search_results = False
            search_context = ""
    elif should_search and not tavily_client:
        # 意图识别要求搜索但搜索服务不可用
        search_attempted = True
        search_failed = True
        has_search_results = False
        print("[搜索结果] ❌ 意图识别要求搜索但搜索服务不可用（tavily_client 未初始化）")
        search_context = "\n\n⚠️ 搜索服务当前不可用。你必须明确告知用户：'抱歉，搜索功能暂时无法使用。' 禁止声称已搜索或编造搜索结果。\n"
    else:
        print(f"[搜索检查] 跳过搜索（意图识别判断不需要搜索）")

    def stream():
        try:
            # 构建消息列表，如果有搜索结果，添加到系统提示词中
            messages_to_send = [{"role": "system", "content": system_prompt}]
            
            # 如果有搜索结果，添加为额外的系统消息（使用更强的语气）
            if search_context and has_search_results:
                print("[系统提示] ✅ 添加搜索结果到系统提示")
                messages_to_send.append({
                    "role": "system",
                    "content": f"""⚠️ 强制要求：以下是联网搜索验证的结果。

{search_context}

你必须：
1. 使用搜索结果中的信息回答用户的问题
2. 如果搜索结果包含歌词，你必须引用真实的歌词
3. 如果用户明确要求搜索，你不能回避或拒绝使用搜索结果
4. 不能编造任何内容，必须基于搜索结果
5. 如果搜索结果不完整，明确说明，但必须使用已有的搜索结果

这是强制要求，不能忽略。"""
                })
            elif search_context and not has_search_results:
                # 搜索执行了但没有结果，明确告知模型
                print("[系统提示] ⚠️ 搜索执行了但没有结果，添加禁止撒谎的提示")
                messages_to_send.append({
                    "role": "system",
                    "content": f"""⚠️ 重要：你刚才尝试执行搜索，但搜索没有返回任何结果。

{search_context}

**严格禁止：**
1. 绝对不能说"根据搜索结果"或"搜索结果显示"等话
2. 绝对不能说"我已经执行了搜索"或"我搜索了"等话（除非明确告知搜索失败）
3. 绝对不能编造搜索结果或假装找到了信息

**正确做法：**
1. 如果搜索超时，明确告知："我尝试搜索了，但搜索超时未能获取结果"
2. 如果搜索没有结果，明确告知："我搜索了相关信息，但没有找到准确的答案"
3. 如果搜索服务不可用，明确告知："抱歉，搜索功能暂时无法使用"
4. 基于你的知识库回答，但必须诚实说明这是基于你的知识，不是搜索结果

记住：诚实比撒谎更重要。"""
                })
            elif search_attempted and search_failed:
                # 尝试了搜索但失败了，明确告知模型
                messages_to_send.append({
                    "role": "system",
                    "content": f"""⚠️ 重要：你刚才尝试执行搜索，但搜索失败了或没有返回结果。

**严格禁止：**
1. 绝对不能说"我已经执行了搜索"或"我搜索了"或"我查了网页"等类似的话
2. 绝对不能说"搜索结果显示"或"根据搜索结果"等
3. 绝对不能编造搜索结果或假装找到了信息

**正确做法：**
1. 如果用户要求搜索，明确告知："抱歉，我无法执行搜索"或"搜索功能暂时不可用"
2. 如果搜索超时，明确告知："我尝试搜索了，但搜索超时未能获取结果"
3. 基于你的知识库回答，但必须诚实说明这是基于你的知识，不是搜索结果

记住：诚实比撒谎更重要。"""
                })
            elif should_search and not search_attempted:
                # 意图识别要求搜索但没有尝试（可能是检测逻辑问题或搜索服务不可用）
                messages_to_send.append({
                    "role": "system",
                    "content": """⚠️ 重要：系统判断需要搜索，但搜索功能没有被触发。

**严格禁止：**
1. 绝对不能说"我已经执行了搜索"或"我搜索了"等
2. 绝对不能编造搜索结果

**正确做法：**
明确告知用户："抱歉，我无法执行搜索功能。但我可以基于我的知识来回答你的问题。"

记住：诚实比撒谎更重要。"""
                })
            
            messages_to_send.extend(history_messages)
            
            completion_stream = client.chat.completions.create(
                model="deepseek-v3.2",
                messages=messages_to_send,
                stream=True,
            )
            collected_chunks: List[str] = []
            try:
                for chunk in completion_stream:
                    if not chunk or not hasattr(chunk, 'choices') or not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    delta = getattr(choice, "delta", None)
                    if delta and getattr(delta, "content", None):
                        # 直接把内容片段写回给前端，由前端累积
                        collected_chunks.append(delta.content)
                        yield delta.content
            except Exception as stream_error:
                print(f"[流式响应] 流式读取错误: {stream_error}")
                import traceback
                traceback.print_exc()
                # 如果流式读取出错，至少返回已收集的内容
                if collected_chunks:
                    yield "".join(collected_chunks)
                # 重新抛出异常，让外层 catch 处理
                raise

            # 流式结束后，将完整对话保存到会话存储中
            assistant_text = "".join(collected_chunks)
            if assistant_text:
                stored_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in history_messages
                ]
                stored_messages.append(
                    {"role": "assistant", "content": assistant_text}
                )
                
                # 保存用户名字：优先使用请求中的名字，其次从对话中提取
                final_user_name = user_name or _extract_user_name(stored_messages, None)
                _save_conversation(conversation_id, stored_messages, final_user_name)
                
                # 检查是否需要取消之前的延迟任务（如果用户继续对话）
                # 然后启动新的5分钟延迟检查任务
                background_tasks.add_task(_check_and_generate_memo, conversation_id, stored_messages, final_user_name, payload.locale)
        except Exception as e:
            # 遇到异常时立即中止，并让前端走兜底逻辑
            raise HTTPException(status_code=500, detail=f"LLM 流式调用失败: {e}") from e

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8")


async def _check_and_generate_memo(conversation_id: str, messages: List[dict], user_name: Optional[str], locale: str):
    """检查是否需要生成手札（5分钟无响应后生成）"""
    import asyncio
    # 等待5分钟
    await asyncio.sleep(300)  # 300秒 = 5分钟
    
    try:
        path = _conversation_path(conversation_id)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 检查最后一条消息的时间
        last_message_time_str = data.get("last_message_time")
        if not last_message_time_str:
            return
        
        try:
            last_message_time = datetime.fromisoformat(last_message_time_str.replace("Z", "+00:00"))
            now = datetime.utcnow().replace(tzinfo=last_message_time.tzinfo)
            time_diff = (now - last_message_time).total_seconds()
            
            # 如果距离最后一条消息已经超过5分钟，且没有新消息，生成手札
            if time_diff >= 300:  # 5分钟 = 300秒
                current_message_count = len(data.get("messages", []))
                last_message_count = data.get("memo_last_message_count", 0)
                
                # 如果消息数量没有增加，说明确实暂停了，生成手札
                if current_message_count > last_message_count:
                    await _generate_and_save_memo(conversation_id, data.get("messages", []), user_name, locale, data)
        except Exception as e:
            print(f"检查手札生成时间失败: {e}")
    except Exception as e:
        print(f"检查手札生成失败: {e}")


async def _generate_and_save_memo(conversation_id: str, messages: List[dict], user_name: Optional[str], locale: str, data: Optional[dict] = None):
    """异步生成并保存手札（支持追加更新，基于会话段）"""
    try:
        path = _conversation_path(conversation_id)
        if data is None:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        existing_memo = data.get("memo")
        last_message_count = data.get("memo_last_message_count", 0)
        current_message_count = len(messages)
        
        # 如果消息数量没有增加，说明没有新对话，不需要更新手札
        if current_message_count <= last_message_count:
            return
        
        # 获取新增的消息（从上次生成手札之后的消息）
        new_messages = messages[last_message_count:] if last_message_count > 0 else messages
        
        # 如果这是第一次生成手札，生成完整的手札
        if not existing_memo or last_message_count == 0:
            conversation_data = {
                "id": conversation_id,
                "messages": messages,
                "user_name": user_name,
                "created_at": data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            }
            memo = await _generate_memo_summary(conversation_data, locale, is_update=False)
            data["memo"] = memo
        else:
            # 如果有已有手札，生成新增对话的摘要并追加
            conversation_data = {
                "id": conversation_id,
                "messages": new_messages,
                "user_name": user_name,
                "created_at": data.get("updated_at", datetime.utcnow().isoformat() + "Z"),
            }
            new_memo_section = await _generate_memo_summary(conversation_data, locale, is_update=True)
            # 追加新手札内容到已有手札
            if locale == "zh":
                data["memo"] = f"{existing_memo}\n\n{new_memo_section}"
            else:
                data["memo"] = f"{existing_memo}\n\n{new_memo_section}"
        
        # 更新消息数量记录和手札生成时间
        data["memo_last_message_count"] = current_message_count
        data["last_memo_time"] = datetime.utcnow().isoformat() + "Z"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # 手札生成失败不影响主流程
        print(f"手札生成失败: {e}")


@app.get("/api/health")
async def health_check() -> dict:
    """简单健康检查，便于调试连通性。"""
    return {"status": "ok", "service": "scent-alchemist-chat-api"}


@app.get("/api/conversations")
async def list_conversations(locale: str = "zh") -> List[dict]:
    """列出已保存的会话，返回原始标题和手札摘要。"""
    items: List[dict] = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(CONVERSATIONS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        
        messages = data.get("messages") or []
        # 使用原始对话的第一条用户消息作为标题
        first_user = next(
            (m.get("content", "") for m in messages if m.get("role") == "user"), ""
        )
        title = first_user[:40] if first_user else (locale == "zh" and "未命名会话" or "Untitled")
        
        items.append(
            {
                "id": data.get("id"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "title": title,
                "memo": data.get("memo"),  # 可选的手札摘要
            }
        )
    # 按更新时间倒序
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return items


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, locale: str = "zh") -> dict:
    """获取单个会话的完整内容，如果还没有手札则生成。"""
    data = _load_conversation(conversation_id)
    
    # 如果还没有手札摘要，生成一个
    if not data.get("memo"):
        memo = await _generate_memo_summary(data, locale)
        data["memo"] = memo
        # 保存到文件
        path = _conversation_path(conversation_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data


class DrawBottleRequest(BaseModel):
    recipe_name: str
    scent_keywords: str
    locale: str = "zh"  # 用于生成描述


@app.post("/api/draw_bottle")
async def draw_bottle(payload: DrawBottleRequest):
    """生成香水瓶视觉设计
    
    流程：
    1. 使用 DeepSeek 将香水名称和香调关键词转化为英文 Stable Diffusion Prompt
    2. 调用百度千帆 FLUX.1-schnell 模型生成图片
    """
    # Step 1: The Translator & Botanical Alchemist - 使用 DeepSeek 翻译并生成复古植物炼金术风格的绘画提示词
    prompt_template = f"""You are a visual prompt engineer for FLUX. Your job is to translate user inputs into a precise ENGLISH visual description in "Vintage Botanical Alchemist" style.

Input:
Name: {payload.recipe_name} (May be Chinese)
Scent: {payload.scent_keywords} (May be Chinese)

Your Task:
1. Translate the Name to a poetic English name (e.g., "破晓" -> "Daybreak", "白金缮" -> "White Kintsugi").
2. Translate the Scent description to English visual keywords focusing on botanical and atmospheric elements.
3. Construct the final prompt strictly following this template:

Final Prompt Template: "A high-quality vintage botanical illustration of a perfume bottle. The bottle is labeled '{{Translated_English_Name}}' in elegant calligraphy. The bottle shape is [shape_based_on_scent]. Surrounding the bottle are hand-drawn sketches of [specific_ingredients] and [atmospheric_elements] (e.g., floating leaves, water drops, sunlight, morning dew, dappled light, smoke wisps, old ink stains). Texture: textured beige paper, pencil lines with soft watercolor washes. Art style: Pierre-Joseph Redouté, elegant, organic, hyper-detailed."

CRITICAL RULES:
- The label text MUST be in English ONLY. NO Chinese characters allowed.
- FORBIDDEN: Do NOT use "molecular structure", "chemical formulas", "benzene rings", "scientific diagrams", or any chemistry-related terms.
- REQUIRED: Focus on "Botanical Illustration" and "Atmospheric Elements".
  * If scent mentions "Rose", use "detailed pencil sketch of dried rose petals".
  * Add atmospheric elements like "morning dew drops", "dappled sunlight", "smoke wisps", "old ink stains", "floating leaves".
- Maximum 512 characters total.
- Output ONLY the final prompt text with all placeholders filled in, nothing else.
- Do NOT include any explanation or additional text."""

    try:
        # 调用 DeepSeek 生成提示词
        completion = client.chat.completions.create(
            model="deepseek-v3.2",
            messages=[
                {"role": "system", "content": "You are a visual prompt engineer for FLUX specializing in Vintage Botanical Alchemist style. You create prompts focused on botanical illustrations and atmospheric elements. NEVER use chemistry-related terms like molecular structures or chemical formulas. Do NOT include any signatures or text in the image (signatures will be added separately). Always output only the final prompt text, no explanations."},
                {"role": "user", "content": prompt_template}
            ],
            temperature=0.7,
            max_tokens=300,
        )
        generated_prompt = completion.choices[0].message.content.strip()
        
        # 移除可能的 markdown 代码块标记和引号
        if "```" in generated_prompt:
            # 移除代码块标记
            if "```" in generated_prompt:
                lines = generated_prompt.split("\n")
                generated_prompt = "\n".join([line for line in lines if not line.strip().startswith("```")])
                generated_prompt = generated_prompt.strip()
        
        # 移除可能的引号包装
        if generated_prompt.startswith('"') and generated_prompt.endswith('"'):
            generated_prompt = generated_prompt[1:-1]
        elif generated_prompt.startswith("'") and generated_prompt.endswith("'"):
            generated_prompt = generated_prompt[1:-1]
        
        # 移除任何中文字符和化学相关词汇（双重保险）
        import re
        # 检查是否包含中文字符
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        # 化学相关关键词列表
        chemistry_keywords = [
            "molecular structure", "chemical formula", "benzene ring", 
            "scientific diagram", "C8H8O3", "C10H12O2", "molecule",
            "chemical", "formula", "structure diagram", "benzene",
            "molecular", "scientific sketch"
        ]
        
        if chinese_pattern.search(generated_prompt):
            # 如果包含中文，尝试提取英文部分
            words = generated_prompt.split()
            english_words = []
            for word in words:
                if not chinese_pattern.search(word):
                    english_words.append(word)
                else:
                    break
            if english_words:
                generated_prompt = " ".join(english_words)
            else:
                # 如果全是中文，使用备用方案（使用植物插画风格）
                generated_prompt = "A high-quality vintage botanical illustration of a perfume bottle in elegant calligraphy. Hand-drawn sketches of botanical elements and atmospheric details. Textured beige paper, pencil lines with soft watercolor washes."
        
        # 移除化学相关词汇，替换为植物插画相关词汇
        for keyword in chemistry_keywords:
            if keyword.lower() in generated_prompt.lower():
                # 替换为植物插画相关词汇
                generated_prompt = re.sub(
                    re.escape(keyword), 
                    "botanical sketches", 
                    generated_prompt, 
                    flags=re.IGNORECASE
                )
        
        # 移除任何签名相关的文本（签名将在前端显示）
        generated_prompt = re.sub(
            r"signed\s+['\"]?le\s+nez['\"]?\s+in\s+the\s+corner\.?", 
            "", 
            generated_prompt, 
            flags=re.IGNORECASE
        )
        generated_prompt = re.sub(
            r"signed\s+['\"].*?['\"]", 
            "", 
            generated_prompt, 
            flags=re.IGNORECASE
        )
        generated_prompt = generated_prompt.strip().rstrip(".,")
        if generated_prompt and not generated_prompt.endswith("."):
            generated_prompt += "."
        
        # 确保提示词不超过 512 字符（FLUX.1-schnell 限制）
        if len(generated_prompt) > 512:
            # 尝试在句号处截断
            last_period = generated_prompt[:512].rfind(".")
            if last_period > 400:  # 至少保留400字符
                generated_prompt = generated_prompt[:last_period + 1]
            else:
                generated_prompt = generated_prompt[:509] + "..."
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prompt: {str(e)}"
        )
    
    # Step 2: The Artist - 调用百度千帆图像生成 API
    IMAGE_MODEL_ID = os.getenv("IMAGE_MODEL_ID", "flux.1-schnell")
    QIANFAN_API_URL = "https://qianfan.baidubce.com/v2/images/generations"
    
    # 获取 API Key（复用 OPENAI_API_KEY，即 bce-v3 开头的 key）
    api_key = OPENAI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured"
        )
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    # 构建请求体
    request_body = {
        "model": IMAGE_MODEL_ID,
        "prompt": generated_prompt,
        "size": "1024x1024",
        "n": 1,
    }
    
    try:
        # 发送 POST 请求到百度千帆
        response = requests.post(
            QIANFAN_API_URL,
            headers=headers,
            json=request_body,
            timeout=60,  # 图像生成可能需要较长时间
        )
        
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", error_detail)
            except:
                pass
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Qianfan API error: {error_detail}"
            )
        
        result = response.json()
        
        # 提取图片 URL
        if "data" in result and len(result["data"]) > 0:
            image_url = result["data"][0].get("url")
            if not image_url:
                raise HTTPException(
                    status_code=500,
                    detail="No image URL in response"
                )
            
            # 生成配方描述和解析前中后调（使用 LLM）
            is_zh = payload.locale == "zh"
            
            # 1. 生成诗意描述
            if is_zh:
                description_prompt = f"""根据香水名「{payload.recipe_name}」和香调关键词「{payload.scent_keywords}」，创作一句诗意描述（包括标点符号在内，严格不超过40字）。

要求：
- 不要直接描述香料成分本身（如"金属醛光"、"玫瑰体乳"等）
- 描述一种生活、一种气息、一种感觉，是这种香料带给人的记忆和情感
- 构建一个场景，描述场景带给人的感觉和氛围，而不是场景中的香料味
- 语言要诗意、抽象、富有想象力，唤起读者的情感共鸣
- 例如：不是"金属醛光穿透被窝"，而是"晨光透过窗帘，唤醒沉睡的梦境"这样的感觉

请创作一句不超过40字的诗意描述。"""
            else:
                description_prompt = f"""Based on the perfume name '{payload.recipe_name}' and scent notes '{payload.scent_keywords}', write a brief, poetic description in English (including punctuation, strictly no more than 40 characters).

Requirements:
- Do not directly describe the scent notes themselves (e.g., "metallic aldehyde", "rose body lotion")
- Describe a way of life, an atmosphere, a feeling—the memories and emotions that these scents evoke
- Build a scene and describe the feelings and atmosphere it brings, not the scent notes in the scene
- Language should be poetic, abstract, and imaginative, evoking emotional resonance
- For example: not "metallic aldehyde light penetrates the covers", but something like "morning light through curtains, awakening sleeping dreams"

Write a poetic description of no more than 40 characters."""
            
            # 2. 解析前中后调（必须使用具体的香味专业词语）
            if is_zh:
                notes_prompt = f"""根据香调关键词「{payload.scent_keywords}」，将其分类为前调、中调、后调。

CRITICAL REQUIREMENTS:
- 必须使用具体的香味专业词语，例如：玫瑰、藏红花、洋甘菊、绿叶、檀木、香皂、茉莉、薰衣草、雪松、琥珀、麝香、香草、柠檬、橙花、广藿香、依兰、鸢尾、紫罗兰、白花、木质、树脂、香料等。
- 绝对禁止使用抽象词语，例如：内敛含蓄、层次丰富、东方美学、平和深邃、禅意意境、优雅、神秘、温暖、清新等。
- 如果关键词可以明确分为前中后调，请按以下格式返回JSON：
  {{"has_notes": true, "top": "具体香味词语1, 具体香味词语2", "middle": "具体香味词语1, 具体香味词语2", "base": "具体香味词语1, 具体香味词语2"}}
- 如果关键词是单一表达（无法区分前中后调），请返回：
  {{"has_notes": false, "single": "具体香味词语1, 具体香味词语2"}}
- 只返回JSON，不要其他解释
- 如果原关键词包含抽象词语，请根据上下文推断并替换为具体的香味专业词语"""
            else:
                notes_prompt = f"""Based on the scent keywords '{payload.scent_keywords}', classify them into top, middle, and base notes.

CRITICAL REQUIREMENTS:
- MUST use specific perfume note terminology, e.g.: rose, saffron, chamomile, green leaves, sandalwood, soap, jasmine, lavender, cedar, amber, musk, vanilla, lemon, neroli, patchouli, ylang-ylang, iris, violet, white flowers, woody, resin, spices, etc.
- ABSOLUTELY FORBIDDEN: abstract terms like "subtle", "rich layers", "elegant", "mysterious", "warm", "fresh", "oriental aesthetics", "peaceful", "profound", "zen", etc.
- If keywords can be clearly divided into top/middle/base notes, return JSON in this format:
  {{"has_notes": true, "top": "specific note 1, specific note 2", "middle": "specific note 1, specific note 2", "base": "specific note 1, specific note 2"}}
- If keywords represent a single expression (cannot be divided), return:
  {{"has_notes": false, "single": "specific note 1, specific note 2"}}
- Return ONLY JSON, no explanations
- If original keywords contain abstract terms, infer and replace them with specific perfume note terminology"""
            
            try:
                # 生成描述
                desc_completion = client.chat.completions.create(
                    model="deepseek-v3.2",
                    messages=[
                        {"role": "system", "content": f"You are a poetic writer specializing in perfume descriptions. Your descriptions focus on emotions, memories, and atmospheres rather than scent notes themselves. Write concise, evocative descriptions that capture the feeling and mood. {'严格控制在40字以内（包括标点符号）' if is_zh else 'Strictly no more than 40 characters (including punctuation)'}."},
                        {"role": "user", "content": description_prompt}
                    ],
                    temperature=0.9,
                    max_tokens=100,
                )
                description = desc_completion.choices[0].message.content.strip()
                # 如果超过40字（中文）或40字符（英文），截断
                if is_zh:
                    if len(description) > 40:
                        for punct in ['。', '，', '、', '；', '：', '.', ',', ';', ':']:
                            idx = description[:40].rfind(punct)
                            if idx > 20:
                                description = description[:idx+1]
                                break
                        else:
                            description = description[:40]
                else:
                    if len(description) > 40:
                        for punct in ['.', ',', ';', ':', '!', '?']:
                            idx = description[:40].rfind(punct)
                            if idx > 20:
                                description = description[:idx+1]
                                break
                        else:
                            description = description[:40]
                
                # 解析前中后调（必须使用具体的香味专业词语）
                notes_completion = client.chat.completions.create(
                    model="deepseek-v3.2",
                    messages=[
                        {"role": "system", "content": "You are a perfume expert. Analyze scent keywords and classify them into perfume notes. CRITICAL: You MUST use specific perfume note terminology (e.g., rose, jasmine, sandalwood, musk, vanilla, citrus, etc.). ABSOLUTELY FORBIDDEN: abstract terms like 'subtle', 'elegant', 'mysterious', 'rich layers', 'oriental aesthetics', etc. Always return valid JSON only."},
                        {"role": "user", "content": notes_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=200,
                )
                notes_text = notes_completion.choices[0].message.content.strip()
                
                # 解析JSON
                import json
                if "```json" in notes_text:
                    notes_text = notes_text.split("```json")[1].split("```")[0].strip()
                elif "```" in notes_text:
                    notes_text = notes_text.split("```")[1].split("```")[0].strip()
                
                notes_data = json.loads(notes_text)
                
            except Exception as e:
                # 如果生成失败，使用默认值
                description = payload.scent_keywords
                if is_zh and len(description) > 40:
                    description = description[:40]
                elif not is_zh and len(description) > 40:
                    description = description[:40]
                # 默认使用单一表达
                notes_data = {
                    "has_notes": False,
                    "single": payload.scent_keywords
                }
            
            # 保存配方
            import time
            recipe_id = f"recipe-{int(time.time() * 1000)}-{''.join([str(ord(c)) for c in payload.recipe_name[:3]])}"
            recipe_data = {
                "id": recipe_id,
                "name": payload.recipe_name,
                "keywords": payload.scent_keywords,
                "description": description,
                "image_url": image_url,
                "created_at": datetime.now().isoformat(),
                "locale": payload.locale,
                "notes": notes_data,  # 添加前中后调信息
            }
            _save_recipe(recipe_id, recipe_data)
            
            return {
                "image_url": image_url,
                "recipe_id": recipe_id,
                "notes": notes_data  # 返回前中后调信息
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from Qianfan API"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Image generation timeout"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request to Qianfan API failed: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


class ExtractRecipeRequest(BaseModel):
    text: str
    locale: str = "zh"  # 默认中文


@app.post("/api/extract_recipe")
async def extract_recipe(payload: ExtractRecipeRequest):
    """从聊天记录或文本中提取香水名和关键词
    
    使用 DeepSeek LLM 从非结构化文本中提取：
    - name: 香水名称（根据 locale 返回对应语言）
    - keywords: 英文视觉关键词（3-5个，始终为英文，用于图像生成）
    """
    is_zh = payload.locale == "zh"
    
    name_instruction = (
        "提取香水名称（如果提到）或根据内容建议一个富有诗意的中文名称"
        if is_zh
        else "Extract the perfume name (if mentioned) or suggest a poetic name in English based on the content"
    )
    
    keywords_instruction = (
        "提取3-5个中文视觉关键词，描述香调的氛围、情绪或视觉元素（例如：潮湿、苔藓、墨水、旧书、电影感光线）。这些关键词将用于图像生成，请确保它们能够准确传达香调的感觉。"
        if is_zh
        else "Extract 3-5 visual keywords in English that describe the mood, atmosphere, or visual elements. Keywords should be suitable for image generation (e.g., 'damp', 'moss', 'ink', 'old books', 'cinematic lighting')"
    )
    
    extract_prompt = f"""Extract the perfume name and 3-5 visual keywords from the following text.

Text:
{payload.text}

Requirements:
- {name_instruction}
- {keywords_instruction}
- Return ONLY valid JSON in this exact format:
{{
  "name": "Perfume Name",
  "keywords": "keyword1, keyword2, keyword3, keyword4, keyword5"
}}

Do not include any explanation or additional text, only the JSON object."""

    try:
        completion = client.chat.completions.create(
            model="deepseek-v3.2",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from text. Always return valid JSON only."},
                {"role": "user", "content": extract_prompt}
            ],
            temperature=0.5,
            max_tokens=200,
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # 尝试解析 JSON（可能包含代码块）
        import json
        # 移除可能的 markdown 代码块标记
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # 验证并返回
        return {
            "name": result.get("name", ""),
            "keywords": result.get("keywords", "")
        }
        
    except json.JSONDecodeError as e:
        # 如果 JSON 解析失败，尝试从文本中提取
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response as JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract recipe: {str(e)}"
        )


@app.get("/api/recipes")
async def list_recipes(locale: str = "zh") -> List[dict]:
    """列出已保存的香水配方"""
    items: List[dict] = []
    for filename in os.listdir(RECIPES_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(RECIPES_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items.append({
                    "id": data.get("id", filename.replace(".json", "")),
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "created_at": data.get("created_at", ""),
                })
        except Exception as e:
            print(f"Error loading recipe {filename}: {e}")
            continue
    
    # 按创建时间倒序排列
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: str) -> dict:
    """获取单个配方的完整内容"""
    return _load_recipe(recipe_id)


class ScentRequest(BaseModel):
    name: str


def get_official_name(user_input: str) -> str:
    """Step 1: 智能别名解析 - 将用户输入（可能是昵称或中文名）转换为官方英文/法文名
    
    Args:
        user_input: 用户输入的香水名称（可能是中文、昵称或部分名称）
    
    Returns:
        官方英文/法文名称，如果转换失败则返回原始输入
    """
    try:
        name_prompt = f"""You are a Perfume Translator. Convert the user's input (which might be a nickname or Chinese name) into the Official English/French Name.

User Input: "{user_input}"

Return ONLY the official perfume name in English or French (e.g., "Louis Vuitton Orage", "Parfums de Marly Delina"). 
If you cannot determine the official name, return the original input unchanged.
Do not include any explanations, just the name."""

        completion = client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a Perfume Translator. Convert perfume names to official English/French names."},
                {"role": "user", "content": name_prompt}
            ],
            temperature=0.2,
            max_tokens=100,
        )
        
        official_name = completion.choices[0].message.content.strip()
        # 清理可能的引号或多余字符
        official_name = official_name.strip('"\'')
        
        print(f"[智能别名解析] 输入: {user_input} -> 输出: {official_name}")
        return official_name
        
    except Exception as e:
        print(f"[智能别名解析] 转换失败: {str(e)}, 使用原始输入")
        import traceback
        traceback.print_exc()
        return user_input


@app.post("/api/analyze_scent")
async def analyze_scent(payload: ScentRequest):
    """分析香水成分 - 使用智能别名解析 + 全网搜索 + DeepSeek 智能验证的 RAG 流程
    
    流程：
    1. 智能别名解析：将用户输入转换为官方英文/法文名
    2. 全网搜索：使用官方名称进行无限制搜索
    3. 智能验证：使用 DeepSeek 提取数据并翻译回中文
    4. 返回结果和参考 URL 列表
    """
    if not TAVILY_AVAILABLE or not tavily_client:
        raise HTTPException(
            status_code=500,
            detail="Tavily Search is not available. Please install tavily-python and set TAVILY_API_KEY"
        )
    
    # Step 1: 智能别名解析 (Name Standardization)
    official_name = get_official_name(payload.name)
    print(f"[Step 1] 智能别名解析完成: {payload.name} -> {official_name}")
    
    # Step 2: 混合全网搜索 (Hybrid Global Search)
    search_results = []
    search_content = ""
    reference_urls = []  # 收集参考 URL
    
    try:
        # 构造英文搜索查询（全网搜索，不限制网站）
        query_en = f"{official_name} perfume notes accords ingredients"
        
        print(f"[Tavily搜索] 开始全网搜索: {query_en}")
        
        # 调用 Tavily API（使用 advanced 深度搜索）
        response = tavily_client.search(
            query=query_en,
            search_depth="advanced",
            max_results=8  # 增加结果数量以提高覆盖率
        )
        
        print(f"[Tavily搜索] 搜索完成，结果数量: {len(response.get('results', []))}")
        
        # 获取搜索结果的 content 摘要
        if response.get("results"):
            for result in response.get("results", [])[:8]:
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                
                if content:
                    search_results.append({
                        "title": title,
                        "content": content,
                        "url": url
                    })
                    # 累积内容摘要
                    search_content += f"Title: {title}\nContent: {content}\nURL: {url}\n\n"
                    # 收集参考 URL
                    if url:
                        reference_urls.append(url)
        
        print(f"[Tavily搜索] 提取到 {len(search_results)} 条有效结果")
        print(f"[Tavily搜索] 参考 URL 数量: {len(reference_urls)}")
    
    except Exception as e:
        # 如果搜索完全失败，不返回错误，而是标记为使用兜底方案
        print(f"[Tavily搜索] 搜索错误: {str(e)}, 将使用空结果")
        import traceback
        traceback.print_exc()
        search_results = []  # 清空结果，触发兜底逻辑
    
    # Step 3: 宽松验证 (Relaxed Validation with Translation)
    # 将 Tavily 的搜索结果喂给 DeepSeek 进行验证和提取
    
    if not search_content or not search_results:
        # 如果没有搜索结果，直接返回未找到
        print(f"[智能验证] 无搜索结果，返回 found: false")
        return {
            "found": False,
            "message": "Perfume not found in search results",
            "reference_urls": []
        }
    
    # 构建验证提示词（支持英文结果并翻译回中文）
    verification_prompt = f"""You are a knowledgeable Perfume Data Analyst.

**Task:** Analyze the search snippets to identify the perfume described by the user's query: "{payload.name}" (official name: "{official_name}").

**CRITICAL RULES:**

**Language Handling:** The search results may be in English, but you must extract data and translate all descriptions back to Chinese for the final JSON output.

**Fuzzy Match:** The user's input might be a nickname, a typo, or a partial name (e.g., "路易威登 雷暴" = "Louis Vuitton Orage").
- If the snippets discuss a perfume that clearly matches the intent (even if the name is slightly different), accept it.
- Example: User says "路易威登 雷暴", Official name is "Louis Vuitton Orage", Snippets show "Louis Vuitton Orage". -> MATCH!
- Example: User says "玛丽之香 玫瑰", Snippets show "Parfums de Marly Delina La Rosée". -> MATCH!

**Correct the Name:** If found, use the official Brand & Name from the snippets in your JSON output (e.g., set "brand": "Louis Vuitton", "name": "Orage / 雷暴").

**Extraction:** Extract all fields (radar_data, notes, etc.) based on the snippets. 
- Translate all descriptions to Chinese.
- Extract notes, accords, and ingredients from English sources.
- Convert radar data scores (0-10) based on the fragrance profile described.

**Not Found:** Only return {{"found": false}} if the snippets are completely unrelated (e.g., about a car or a politician) or "No results found".

**Search snippets:**
{search_content}

Return ONLY valid JSON, no explanations, no markdown code blocks."""
    
    system_prompt = """You are a knowledgeable Perfume Data Analyst.

**Task:** Analyze the search snippets to identify the perfume described by the user's query.

**CRITICAL RULES:**

**Language Handling:** The search results may be in English, but you must extract data and translate all descriptions back to Chinese for the final JSON output.

**Fuzzy Match:** The user's input might be a nickname, a typo, or a partial name (e.g., "路易威登 雷暴" = "Louis Vuitton Orage").
- If the snippets discuss a perfume that clearly matches the intent (even if the name is slightly different), accept it.
- Example: User says "路易威登 雷暴", Official name is "Louis Vuitton Orage", Snippets show "Louis Vuitton Orage". -> MATCH!

**Correct the Name:** If found, use the official Brand & Name from the snippets in your JSON output (e.g., set "brand": "Louis Vuitton", "name": "Orage / 雷暴").

**Extraction:** Extract all fields (radar_data, notes, etc.) based on the snippets. Translate descriptions to Chinese.

**Not Found:** Only return {"found": false} if the snippets are completely unrelated (e.g., about a car or a politician) or "No results found".

**MANDATORY Output JSON Structure (when found=true):**
{
  "found": true,
  "brand": "品牌名 (bilingual format)",
  "name": "香水名 (bilingual format: English Name / 中文名)",
  "radar_data": {
    "Floral": 0-10,
    "Woody": 0-10,
    "Fresh": 0-10,
    "Spicy": 0-10,
    "Sweet": 0-10,
    "Oriental": 0-10
  },
  "notes": {
    "top": "前调描述 (中文)",
    "middle": "中调描述 (中文)",
    "base": "后调描述 (中文)"
  },
  "allergens": ["Limonene", "Linalool"],
  "longevity": "留香时间 (e.g., '持久 8h+')",
  "safety_brief": "安全简评 (中文)"
}

Always return valid JSON only."""
    
    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": verification_prompt}
            ],
            temperature=0.3,
            max_tokens=1500,  # 增加 token 限制以支持更详细的数据
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # 调试日志：打印 LLM 原始响应
        print(f"[DeepSeek验证] LLM 原始响应: {response_text}")
        
        # 解析 JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        print(f"[DeepSeek验证] 解析后的 JSON 字符串: {response_text}")
        
        result = json.loads(response_text)
        
        print(f"[DeepSeek验证] 解析后的 JSON 对象: found={result.get('found', False)}")
        
        # 添加来源标记和参考 URL
        result["source"] = "tavily_verified"
        result["reference_urls"] = reference_urls[:5]  # 最多返回 5 个参考 URL
        
        # 验证结果
        if not result.get("found", False):
            return {
                "found": False,
                "message": "Perfume not found in search results",
                "source": "tavily_verified",
                "reference_urls": reference_urls[:5]
            }
        
        # 返回结果
        return result
        
    except json.JSONDecodeError as e:
        print(f"[智能验证] JSON 解析失败: {str(e)}")
        return {
            "found": False,
            "message": f"Failed to parse analysis: {str(e)}",
            "source": "tavily_verified",
            "reference_urls": reference_urls[:5]
        }
    except Exception as e:
        print(f"[智能验证] LLM 调用失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "found": False,
            "message": f"Analysis failed: {str(e)}",
            "source": "tavily_verified",
            "reference_urls": reference_urls[:5]
        }


# 启动服务器
if __name__ == "__main__":
    import uvicorn  # pyright: ignore[reportMissingImports]
    uvicorn.run(app, host="0.0.0.0", port=8001)
