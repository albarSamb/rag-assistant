<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useDocumentsStore } from '../stores/documents'
import ChatMessage from '../components/chat/ChatMessage.vue'
import ChatInput from '../components/chat/ChatInput.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()
const docs = useDocumentsStore()

const messagesContainer = ref(null)
const selectedDocFilter = ref(null)

const conversationId = computed(() => route.params.id)

onMounted(() => {
  docs.fetchDocuments()
  chat.fetchConversations()
})

watch(conversationId, async (id) => {
  selectedDocFilter.value = null
  if (id) {
    await chat.selectConversation(id)
    scrollToBottom()
  } else {
    chat.currentConversation = null
    chat.messages = []
  }
}, { immediate: true })

watch(() => chat.messages.length, () => {
  nextTick(scrollToBottom)
})

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function handleSend(content) {
  if (!chat.currentConversation) {
    const conv = await chat.createConversation(content.slice(0, 50))
    if (conv) {
      router.replace(`/chat/${conv.id}`)
    }
  }
  await chat.sendMessage(content, selectedDocFilter.value)
}
</script>

<template>
  <div class="flex-1 flex flex-col h-full">
    <!-- Header -->
    <header class="flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">
          {{ chat.currentConversation?.title || 'Nouvelle conversation' }}
        </h1>
        <p class="text-xs text-gray-500">Posez vos questions sur la documentation</p>
      </div>
      <div class="flex items-center gap-3">
        <select
          v-model="selectedDocFilter"
          class="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option :value="null">Tous les documents</option>
          <option
            v-for="doc in docs.documents.filter(d => d.processing_status === 'completed')"
            :key="doc.id"
            :value="doc.id"
          >
            {{ doc.original_name }}
          </option>
        </select>
      </div>
    </header>

    <!-- Messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
      <!-- Empty state -->
      <div v-if="chat.messages.length === 0 && !chat.loading" class="flex-1 flex items-center justify-center h-full">
        <div class="text-center max-w-md">
          <div class="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-gray-900 mb-2">Posez votre question</h2>
          <p class="text-gray-500 text-sm">
            Interrogez votre documentation technique en langage naturel.
            Les reponses seront basees sur vos documents uploades.
          </p>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="chat.loading" class="flex justify-center py-8">
        <LoadingSpinner size="lg" />
      </div>

      <!-- Messages -->
      <ChatMessage
        v-for="msg in chat.messages"
        :key="msg.id"
        :message="msg"
      />
    </div>

    <!-- Input -->
    <ChatInput
      @send="handleSend"
      :disabled="chat.streaming"
    />
  </div>
</template>
