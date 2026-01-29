<script setup>
import { ref } from 'vue'
import { Send, Bot, User, ShieldCheck } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'
import axios from 'axios'

const md = new MarkdownIt()
const userInput = ref('')
const messages = ref([
  { role: 'assistant', content: 'Bonjour ! Je suis votre expert **Veille RGPD**. Posez-moi une question sur les délibérations de la CNIL.' }
])
const isLoading = ref(false)
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = userInput.value
  
  messages.value.push({ role: 'user', content: userMessage })
  
  userInput.value = ''
  isLoading.value = true

  try {
    const response = await axios.post('http://localhost:8000/chat', {
      message: userMessage 
    })

    messages.value.push(response.data)

  } catch (error) {
    console.error("Détails de l'erreur:", error.response?.data)
    messages.value.push({ 
      role: 'assistant', 
      content: "Désolé, une erreur est survenue." 
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">
        <div class="icon-box"><ShieldCheck :size="20" color="white" /></div>
        <span>RGPD AI <small>Pulse</small></span>
      </div>
      <div class="badge">API Légifrance</div>
    </header>

    <main class="chat-area">
      <div class="messages-wrapper">
        <div v-for="(msg, i) in messages" :key="i" :class="['message-row', msg.role]">
          <div class="avatar">
            <Bot v-if="msg.role === 'assistant'" :size="20" />
            <User v-else :size="20" />
          </div>
          <div class="content" v-html="md.render(msg.content)"></div>
        </div>
        
        <div v-if="isLoading" class="loader">Reflexion...</div>
      </div>
    </main>

    <footer class="app-footer">
      <div class="input-container">
        <textarea 
          v-model="userInput" 
          placeholder="Votre question juridique..."
          @keydown.enter.prevent="sendMessage"
        ></textarea>
        <button @click="sendMessage" :disabled="!userInput">
          <Send :size="22" />
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #131314;
  color: #e3e3e3;
  font-family: 'Segoe UI', Roboto, sans-serif;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  border-bottom: 1px solid #3c4043;
}
.logo { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 600; }
.icon-box { background: linear-gradient(135deg, #4285f4, #9b51e0); padding: 5px; border-radius: 8px; display: flex; }
.badge { font-size: 0.7rem; background: #2e2f30; padding: 4px 12px; border-radius: 20px; color: #aaa; border: 1px solid #444; }

.chat-area { flex: 1; overflow-y: auto; padding: 2rem 1rem; }
.messages-wrapper { max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 2.5rem; }

.message-row { display: flex; gap: 20px; align-items: flex-start; }
.avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.assistant .avatar { background: #1a73e8; color: white; }
.user .avatar { background: #444746; color: white; }

.content { line-height: 1.6; font-size: 15px; }
.content :deep(strong) { color: #8ab4f8; }

.app-footer { padding: 1rem 1rem 2rem; }
.input-container {
  max-width: 800px;
  margin: 0 auto;
  background: #1e1f20;
  border-radius: 28px;
  display: flex;
  align-items: center;
  padding: 0.5rem 1.5rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: white;
  padding: 12px 0;
  resize: none;
  outline: none;
  font-size: 16px;
  height: 48px;
}
button {
  background: transparent;
  border: none;
  color: #8ab4f8;
  cursor: pointer;
  padding: 8px;
  transition: opacity 0.2s;
}
button:disabled { opacity: 0.3; cursor: not-allowed; }

.loader { font-size: 0.8rem; color: #888; font-style: italic; margin-left: 56px; }
</style>