import os
from langchain_openai import ChatOpenAI

# 1. Set variables strictly (without quotes in the value)
os.environ["OPENAI_API_KEY"] = "3a079847-04f4-4315-a8bd-d31b29d83d4a"
os.environ["SCW_PROJECT_ID"] = "aac73328-9d61-47b4-ae1c-3014e3ea7661"

# 2. Re-instantiate the LLM with the corrected environment variables
llm = ChatOpenAI(
    model="pixtral-12b-2409",  # safe, fast, free-tier compatible
    base_url="https://api.scaleway.ai/v1",
    api_key=os.environ["OPENAI_API_KEY"],
    default_headers={
        "X-Project-ID": os.environ["SCW_PROJECT_ID"]
    },
    temperature=0,
    max_tokens=100,
    streaming=False
)

# 3. Initialize conversation history
conversation_history = []

def send_message(user_input):
    # Append user message to history
    conversation_history.append({"role": "user", "content": user_input})
    
    # Send full conversation history to LLM
    response = llm.invoke(conversation_history)
    
    # Append LLM response to history
    conversation_history.append({"role": "assistant", "content": response.content})
    
    return response.content


def clear_history():
    global conversation_history
    conversation_history = []

initMsg = "Tu es un assistant juridique IA capable d’aider une organisation à structurer et exploiter une veille RGPD à partir de sources publiques en ligne. L’objectif est de transformer des textes juridiques, des communiqués ou des décisions en informations compréhensibles, actionnables et adaptées à différents profils. Réponds aux questions de l'utilisateur en fonction de son profil. Profil utilisateur : Ingénieur développement"
# ex : DSI, DPO, dirigeant, chef de projet


conversation_history.append({"role": "system", "content": initMsg})
