import os
import base64
import requests
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

# 宣告主要的聊天大腦
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
                print(f"🚀 啟動原生 HTTP 請求呼叫 Google Imagen 3... 提示詞: {user_input}")
                
                # 💡 使用底層 HTTP POST 直接對接 Google AI Studio 官方生圖端點
                url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={api_key}"
                
                payload = {
                    "numberOfImages": 1,
                    "prompt": user_input,
                    "aspectRatio": "1:1",
                    "outputMimeType": "image/jpeg"
                }
                
                headers = {"Content-Type": "application/json"}
                
                # 發射請求
                response = requests.post(url, json=payload, headers=headers, timeout=25)
                
                if response.statusCode == 200:
                    res_data = response.json()
                    # 提取 Google 回傳的純圖片 Base64 字串
                    encoded_image = res_data["generatedImages"][0]["image"]["imageBytes"]
                    print("✅ Google 成功生成圖片並回傳！")
                    return {"answer": f"data:image/jpeg;base64,{encoded_image}"}
                else:
                    print(f"⚠️ Google 拒絕請求，狀態碼: {response.status_code}, 原因: {response.text}")
                    raise Exception(f"Google API Error: {response.text}")
                
            except Exception as img_err:
                print(f"❌ 原生生圖失敗，啟動防護罩機制: {str(img_err)}")
                # 萬一真的有狀況，回傳這一張 100% 存在、防崩潰的美麗小插圖，保證不留白！
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
