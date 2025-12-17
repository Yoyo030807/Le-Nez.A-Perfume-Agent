// 自动判断环境：
// - 生产环境 (PROD): 使用 Render 的云端地址
// - 开发环境 (DEV): 使用本地后端的 8001 端口
export const API_BASE_URL = import.meta.env.PROD 
  ? 'https://le-nez-a-perfume-agent.onrender.com' 
  : 'http://localhost:8001';