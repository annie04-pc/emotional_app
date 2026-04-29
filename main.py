import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# 1. CORS 設定：允許 Flutter Web (Netlify) 跨域存取
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini 配置與環境變數檢查
# 在 Render 的 Environment 務必設定 GEMINI_API_KEY
api_key = os.getenv("GEMINI_API_KEY")

# 監視器：會在 Render 的 Logs 裡印出狀態
if api_key:
    print(f"✅ 成功讀取 API Key (前五碼)")
else:
    print("❌ 錯誤：完全沒抓到 GEMINI_API_KEY，請確認 Render 環境變數設定！")

genai.configure(api_key=api_key)

# 設定 AI 角色定位 (System Instruction)
# 1. 改用最基本的名稱，不要加 models/，也不要加額外參數
model_name = "gemini-3-flash" 

# 2. 在日誌印出正在啟用的模型名稱（方便我們在 Log 檢查有沒有多空格）
print(f"🤖 正在啟動 AI 模型: [{model_name}]")

model = genai.GenerativeModel(model_name)

# 3. 妳的 System Instruction 改到 generate_content 裡面，或是先拿掉測試
# 為了最快除錯，我們先用最陽春的設定

class ChatRequest(BaseModel):
    question: str

# 3. 聊天 API 接口
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 呼叫 Gemini 產生內容
        response = model.generate_content(request.question)

        # 🛡️ 關鍵安全檢查：避免 'candidates' 報錯
        # 如果 AI 沒回傳答案 (可能是被安全過濾攔截)
        if response and response.candidates and len(response.candidates) > 0:
            return {"answer": response.text}
        else:
            return {"answer": "AI 暫時無法回應，請試著用更溫和的方式提問。"}

    except Exception as e:
        # 將詳細錯誤印在雲端日誌，方便除錯
        print(f"Chat Error Detail: {str(e)}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤，請檢查 Logs")

# 4. 心跳檢查 (確認伺服器活著)
@app.get("/")
async def root():
    return {"status": "online", "message": "AINI Backend Server is Running"}