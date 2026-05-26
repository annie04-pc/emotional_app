import os
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# 1. CORS 設定：允許跨域存取
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Gemini 配置與環境變數檢查
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    print(f"✅ 成功讀取 API Key (前五碼)")
else:
    print("❌ 錯誤：完全沒抓到 GEMINI_API_KEY，請確認 Render 環境變數設定！")

genai.configure(api_key=api_key)

# 宣告主要模型
model_name = "gemini-2.5-flash" 
print(f"🤖 正在啟動 AI 模型: [{model_name}]")
chat_model = genai.GenerativeModel(model_name)

class ChatRequest(BaseModel):
    question: str
    is_image_gen: bool = False  # 💡 新增一個欄位，讓前端可以主動告知「這是生圖請求」

# 3. 聊天與生圖共用 API 接口
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        user_input = request.question.strip()
        
        # 🎨 路線 A：如果前端標記是生圖，或者使用者輸入包含畫圖關鍵字
        if request.is_image_gen or "畫" in user_input or "生成" in user_input:
            try:
                print(f"🎨 偵測到生圖指令，正在啟用 Imagen 3 繪圖模型... 提示詞: {user_input}")
                
                # 調用 Google 官方最新、最契合免費方案的 Imagen 3 模型
                imagen_model = genai.ImageGenerationModel("imagen-3.0-generate-002")
                
                result = imagen_model.generate_images(
                    prompt=user_input,
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"  # 正方形比例，完美契合妳前端的 Container 尺寸
                )
                
                # 將圖片轉為 Base64 字串
                image_bytes = result.images[0].image.bytes
                encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # 把 Base64 網址包裝在 answer 欄位回傳給前端 [cite: 2]
                return {"answer": f"data:image/jpeg;base64,{encoded_image}"}
                
            except Exception as img_err:
                print(f"❌ Imagen 生圖失敗，切換回普通文字回應: {str(img_err)}")
                # 萬一繪圖被安全封鎖，回退給文字模型告知用戶
                return {"answer": f"生圖失敗，因為触发了安全过濾機制或額度限制：{str(img_err)}"}

        # 💬 路線 B：正常的普通 AI 諮商對話
        print(f"💬 正常的諮商對話: {user_input}")
        response = chat_model.generate_content(user_input)

        if response and response.candidates and len(response.candidates) > 0:
            return {"answer": response.text} 
        else:
            return {"answer": "AI 暫時無法回應，請試著用更溫和的方式提問。"} 

    except Exception as e:
        print(f"Chat Error Detail: {str(e)}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤，請檢查 Logs")

# 4. 心跳檢查 (確認伺服器活著)
@app.get("/")
async def root():
    return {"status": "online", "message": "AINI Backend Server is Running"}
