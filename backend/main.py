import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

app = FastAPI()

# --- CONFIGURATION CORS (Pour autoriser votre Vue.js) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION LLM ---
os.environ["LLM_ENDPOINT"] = "http://open-webui-service.vllm.svc:8080/api"
os.environ["LLM_SECRET_KEY"] = "sk-7724b0d24dc24753843cc5ec11125db7"

llm = ChatOpenAI(
    model="mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    base_url=os.environ["LLM_ENDPOINT"],
    api_key=os.environ["LLM_SECRET_KEY"],
    temperature=0,
    max_tokens=2000,
)

# Modèle de données pour la requête
class ChatRequest(BaseModel):
    message: str
@app.post("/chat") # Assure-toi que l'URL correspond au front
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [
            {"role": "system", "content": "Tu es un expert en veille RGPD et délibérations de la CNIL."},
            {"role": "user", "content": request.message}
        ]
        
        response = llm.invoke(messages)
        
        # On renvoie le format attendu par ton front (avec role et content)
        return {
            "role": "assistant",
            "content": response.content
        }
    
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Erreur backend : {str(e)}"
        }