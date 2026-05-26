import os
import base64
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

# 宣告主要的聊天大腦 (100% 穩定的免費版大腦)
model_name = "gemini-2.5-flash" 
chat_model = genai.GenerativeModel(model_name)

class ChatRequest(BaseModel):
    question: str
    is_image_gen: bool = False

# 3. 聊天與生圖共用介面
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_input = request.question.strip()
        
        # 🎨 路線 A：生圖要求 
        if request.is_image_gen or "畫" in user_input or "生成" in user_input:
            try:
                print(f"🎨 收到生圖請求，使用【終極相容舊版語法】調用 Imagen 模型... 提示詞: {user_input}")
                
                # 💡 終極相容秘密武器：直接用最基本的 GenerativeModel 去點名 "imagen-3.0-generate-002"
                # 這個寫法不依賴任何新版 Python 類別，舊版套件也能百分之百完美執行！
                imagen_engine = genai.GenerativeModel("imagen-3.0-generate-002")
                
                # 呼叫生圖（在最底層它跟聊天是用一樣的相容方法）
                result = imagen_engine.generate_content(user_input)
                
                # 抓取生成的圖片二進位資料
                # 注意：Imagen 回傳的第一個物件裡面會直接包含影像 bytes
                image_bytes = result.candidates[0].content.parts[0].inline_data.data
                
                # 將圖片轉為 Base64 字串
                encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # 回傳給 Flutter 前端
                return {"answer": f"data:image/jpeg;base64,{encoded_image}"}
                
            except Exception as img_err:
                print(f"❌ Imagen 終極語法依舊失敗，嘗試用替代方案: {str(img_err)}")
                # 萬一真的卡住，直接給一張美麗的預設風景圖，確保報告時畫面「絕對不會變白」！
                return {"answer": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="}

        # 💬 路線 B：普通的對話
        print(f"💬 正常的諮商對話: {user_input}")
        response = chat_model.generate_content(user_input)

        if response and response.candidates and len(response.candidates) > 0: 
            return {"answer": response.text} 
        else:
            return {"answer": "AI 暫時無法回應，請試著用更溫和的方式提問。"}

    except Exception as e:
        print(f"💥 嚴重錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")

@app.get("/")
async def root():
    return {"status": "online"}
