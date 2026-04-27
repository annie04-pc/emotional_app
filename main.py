from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn

app = FastAPI()

# 💡 解決 Flutter Web 連線的跨來源限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💡 這裡請填入妳在 Google AI Studio 申請的 API Key
GOOGLE_API_KEY = "AIzaSyC2RxcXiOxoHSUyVLA4lYEtFU7U7ikZIkc"

@app.post("/chat")
async def chat_endpoint(payload: dict):
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="未收到問題內容")

    # 呼叫 Gemini 文字生成服務
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GOOGLE_API_KEY}"
    
    try:
        response = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": question}]}],
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }
        )
        res_json = response.json()
        # 從 Google 回傳的格式中解析出文字
        answer = res_json['candidates'][0]['content']['parts'][0]['text']
        return {"answer": answer}
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image")
async def image_gen_endpoint(payload: dict):
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="未收到描述詞")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3:generateImages?key={GOOGLE_API_KEY}"
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Image Gen Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "online", "message": "AINI Backend Server is Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)