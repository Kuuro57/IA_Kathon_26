import requests
import chromadb
from chromadb.utils import embedding_functions
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime, timedelta
import time
import re

# --- CONFIGURATION ---
CHROMA_PATH = "./chroma_db_rgpd"
COLLECTION_NAME = "rgpd_knowledge"

# --- INITIALISATION ---
client = chromadb.PersistentClient(path=CHROMA_PATH)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=emb_fn)

def split_text(text):
    return RecursiveCharacterTextSplitter(
        chunk_size=800, # Chunks plus petits pour plus de précision
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "]
    ).split_text(text)

def extract_content(item):
    """Fusionne les champs textuels de l'API pour maximiser la matière du RAG"""
    fields = ['descriptionFusionHtml', 'resumePrincipal', 'texte']
    text = " ".join([clean_html(item.get(f, '')) for f in fields])
    
    # Exploration des sections d'articles si disponibles
    for sec in item.get('sections', []):
        for art in sec.get('articles', []):
            text += f"\n {art.get('text', '')}"
    return text.strip()

def clean_html(html):
    if not html: return ""
    return BeautifulSoup(html, 'html.parser').get_text(separator=" ", strip=True)

def add_to_db(docs):
    for doc in docs:
        if not doc or len(doc['content']) < 200: continue
        
        chunks = split_text(doc['content'])
        ids = [f"{doc['url']}_{i}" for i in range(len(chunks))]
        metas = [{
            "source": doc['url'], "title": doc['title'], "type": doc['source_type'],
            "date": str(doc.get('date', ''))
        } for _ in chunks]
        
        collection.add(documents=chunks, metadatas=metas, ids=ids)

def discover_cnil_links():
    """Trouve dynamiquement les derniers articles sur la page actu de la CNIL"""
    base = "https://www.cnil.fr"
    try:
        res = requests.get(f"{base}/fr/actualites", timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        links = []
        # On cherche tous les liens qui mènent à des actualités ou des sanctions
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/fr/actualite" in href or "/fr/sanction" in href:
                full_url = base + href if href.startswith('/') else href
                if full_url not in links: links.append(full_url)
        return links[:10] # On prend les 10 derniers
    except:
        return []

def mine_data():
    print("Extraction des données CNIL (Source officielle)...")
    dynamic_links = discover_cnil_links()

    all_links = list(set(dynamic_links + [
        "https://www.cnil.fr/fr/reglement-europeen-protection-donnees",
        "https://www.cnil.fr/fr/les-sanctions-prononcees-par-la-cnil",
        "https://www.cnil.fr/fr/la-securite-des-donnees",
        "https://www.cnil.fr/fr/principes-cles/les-bases-legales",
        "https://www.cnil.fr/fr/principes-cles/guide-de-la-securite-des-donnees-personnelles",
        "https://www.cnil.fr/fr/loi-informatique-et-libertes"
    ]))
    
    docs = []
    for url in all_links:
        try:
            print(f"Analyse de : {url.split('/')[-1]}")
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # Extraction propre du contenu
            main = soup.find('main') or soup.article or soup
            text = " ".join([p.get_text() for p in main.find_all(['p', 'li', 'h2']) if len(p.get_text()) > 30])
            
            docs.append({
                "title": soup.title.string.split('|')[0].strip(),
                "url": url, 
                "content": text, 
                "source_type": "CNIL (Officiel)"
            })
        except:
            continue
    
    if docs:
        add_to_db(docs)

if __name__ == "__main__":
        mine_data()
        print(f"Base prête : {collection.count()} vecteurs.")