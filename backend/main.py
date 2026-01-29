import os
import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

CHROMA_PATH = "./chroma_db_rgpd"
COLLECTION_NAME = "rgpd_knowledge"

client = chromadb.PersistentClient(path=CHROMA_PATH)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=emb_fn)

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
initMsg = (
    "Tu es un assistant juridique IA capable d’aider une organisation à structurer et exploiter "
    "une veille RGPD à partir de sources publiques en ligne. L’objectif est de transformer des "
    "textes juridiques, des communiqués ou des décisions en informations compréhensibles, "
    "actionnables et adaptées à différents profils. Réponds aux questions de l'utilisateur "
    "en fonction de son profil. Profil utilisateur : Ingénieur développement"
)

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
        # 1. RECHERCHE DANS CHROMADB (Le "R" de RAG)
        # On cherche les 3 passages les plus pertinents par rapport à la question
        results = collection.query(
            query_texts=[request.message],
            n_results=3
        )
        
        # 2. CONSTRUCTION DU CONTEXTE
        # On assemble les documents trouvés pour les donner au LLM
        context_docs = ""
        if results['documents'] and results['documents'][0]:
            context_docs = "\n\n".join(results['documents'][0])
        
        # 3. ENRICHISSEMENT DU MESSAGE (Prompt Engineering)
        # On demande au LLM d'utiliser uniquement ces infos
        rag_prompt = f"""CONTEXTE OFFICIEL (CNIL) :
        {context_docs}

        QUESTION UTILISATEUR :
        {request.message}

        CONSIGNE : Réponds à la question en utilisant exclusivement le contexte ci-dessus."""

        # 4. GESTION DE L'HISTORIQUE ET APPEL
        conversation_history.append({"role": "user", "content": rag_prompt})
        
        response = llm.invoke(conversation_history)
        
        # On nettoie l'historique pour ne pas stocker le gros bloc de contexte 
        # mais seulement la réponse propre pour la suite de la conversation
        conversation_history.pop() # Enlève le gros message avec contexte
        conversation_history.append({"role": "user", "content": request.message})
        conversation_history.append({"role": "assistant", "content": response.content})
        
        return {
            "role": "assistant",
            "content": response.content
        }
    
    except Exception as e:
        return {"role": "assistant", "content": f"Erreur RAG : {str(e)}"}

@app.post("/clear")
async def clear_endpoint():
    global conversation_history
    conversation_history = [{"role": "system", "content": initMsg}]
    return {"status": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)