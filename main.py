import os
import urllib.parse
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# 1. CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini 配置
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 宣告主要的 100% 穩定對話大腦
model_name = "gemini-2.5-flash" 
chat_model = genai.GenerativeModel(model_name)

class ChatRequest(BaseModel):
    question: str
    is_image_gen: bool = False

# 📋 💥 新增：量表資料傳送格式（對齊手機前端欄位）
class ScalePayload(BaseModel):
    userId: str
    userName: str
    totalScore: int
    createdTime: str
    detailJson: str

# 🗄️ 💥 新增：量表專用暫存記憶體陣列
SCALE_DATABASE = []


# 3. 聊天與生圖共用介面
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_input = request.question.strip()
        
        # 🎨 路線 A：生圖要求
        if request.is_image_gen or "畫" in user_input or "生成" in user_input:
            try:
                print(f"🔮 啟動智慧美圖生成引擎... 提示詞: {user_input}")
                
                prompt = (
                    f"請將以下這句話『{user_input}』轉化為 2 到 3 個最精準的英文攝影關鍵字。"
                    f"只需要輸出英文單字，用逗號隔開，絕對不要包含任何其他解釋、標點符號或中文字。"
                    f"例如：輸入『一個彩色的生日蛋糕』，妳只需要輸出『colorful,birthday,cake』。"
                )
                
                response = chat_model.generate_content(prompt)
                keywords = response.text.strip().replace(" ", "")
                
                safe_keywords = urllib.parse.quote(keywords)
                
                rand_num = random.randint(1, 1000)
                image_url = f"https://images.unsplash.com/photo-{rand_num}?auto=format&fit=crop&w=800&q=80&sig={rand_num}&q={safe_keywords}"
                
                print(f"✅ 成功生成動態設計感美圖網址: {image_url}")
                return {"answer": image_url}
                
            except Exception as img_err:
                print(f"❌ 智慧生圖失敗，啟動防護罩預設圖: {str(img_err)}")
                return {"answer": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97"}

        # 💬 路線 B：普通的諮商對話
        print(f"💬 正常的諮商對話: {user_input}")
        response = chat_model.generate_content(user_input)

        if response and response.candidates and len(response.candidates) > 0:
            return {"answer": response.text}
        else:
            return {"answer": "AI 暫時無法回應，請試著用更溫和的方式提問。"}

    except Exception as e:
        print(f"💥 嚴重錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")


# 📥 💥 新增：接收手機量表提交的路由
@app.post("/save_scale")
async def save_scale(payload: ScalePayload):
    try:
        SCALE_DATABASE.append({
            "userId": payload.userId,
            "userName": payload.userName,
            "totalScore": payload.totalScore,
            "createdTime": payload.createdTime,
            "detailJson": payload.detailJson
        })
        print(f"📈 成功儲存一筆新量表：{payload.userName}，總分：{payload.totalScore} 分")
        return {"status": "success", "message": "量表紀錄儲存成功"}
    except Exception as e:
        print(f"❌ 儲存量表失敗: {str(e)}")
        return {"status": "error", "message": str(e)}


# 📤 💥 新增：提供管理員後台讀取全部紀錄的路由
@app.get("/get_scale_records")
async def get_scale_records():
    print(f"🔍 後台正在調閱量表紀錄，目前累計：{len(SCALE_DATABASE)} 筆")
    return {"records": SCALE_DATABASE}


@app.get("/")
async def root():
    return {"status": "online"}
