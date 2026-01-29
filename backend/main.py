import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

app = FastAPI()

# --- CONFIGURATION CORS ---
# On autorise localhost:5173 (Vue) et 127.0.0.1 pour éviter les erreurs de navigateur
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION LLM (Scaleway) ---
os.environ["OPENAI_API_KEY"] = "3a079847-04f4-4315-a8bd-d31b29d83d4a"
os.environ["SCW_PROJECT_ID"] = "aac73328-9d61-47b4-ae1c-3014e3ea7661"

llm = ChatOpenAI(
    model="pixtral-12b-2409",
    base_url="https://api.scaleway.ai/v1",
    api_key=os.environ["OPENAI_API_KEY"],
    default_headers={
        "X-Project-ID": os.environ["SCW_PROJECT_ID"]
    },
    temperature=0,
    max_tokens=500, # Augmenté car 100 est très court pour des réponses juridiques
    streaming=False
)

# --- LOGIQUE DE CONVERSATION ---
# Note : En l'état, cette liste est partagée par tous les utilisateurs (global).
# Pour un vrai chatbot multi-utilisateurs, il faudrait une gestion par session.
initMsg = "Tu es un assistant juridique IA capable d’aider une organisation à structurer et exploiter une veille RGPD à partir de sources publiques en ligne. L’objectif est de transformer des textes juridiques, des communiqués ou des décisions en informations compréhensibles, actionnables et adaptées à différents profils. Réponds aux questions de l'utilisateur en fonction de son profil. Ton rôle est de synthétiser l’information juridique et réglementaire, de mettre en évidence les obligations, risques et bonnes pratiques et d'expliciter les limites, incertitudes et non-substituabilité à un avis juridique. Réponds aux questions en utilisant exclusivement le contexte ci-dessus, issu du site internet de la CNIL. Si l'information n'est pas dans le contexte, précise-le. Profil utilisateur : Ingénieur développement"
conversation_history = [
    {"role": "system", "content": initMsg}
]

# Modèle de données pour la requête
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global conversation_history
    try:
        # 1. Ajouter le message de l'utilisateur à l'historique
        conversation_history.append({"role": "user", "content": request.message})
        
        # 2. Appeler le LLM avec l'historique complet
        response = llm.invoke(conversation_history)
        
        # 3. Ajouter la réponse de l'assistant à l'historique
        conversation_history.append({"role": "assistant", "content": response.content})
        
        # 4. Renvoyer la réponse au format attendu par Vue.js
        return {
            "role": "assistant",
            "content": response.content
        }
    
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Erreur backend : {str(e)}"
        }

@app.post("/clear")
async def clear_endpoint():
    global conversation_history
    conversation_history = [{"role": "system", "content": initMsg}]
    return {"status": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)