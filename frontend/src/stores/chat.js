import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import api from '../services/api'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConversation = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const streaming = ref(false)
  const error = ref(null)

  async function fetchConversations() {
    try {
      const { data } = await api.get('/chat/')
      conversations.value = data.conversations
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load conversations'
    }
  }

  async function createConversation(title) {
    try {
      const { data } = await api.post('/chat/', { title })
      conversations.value.unshift(data)
      currentConversation.value = data
      messages.value = []
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to create conversation'
      return null
    }
  }

  async function selectConversation(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/chat/${id}`)
      currentConversation.value = data
      messages.value = data.messages || []
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load conversation'
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(content, documentFilter = null) {
    if (!currentConversation.value) return

    // Add user message to UI immediately
    messages.value.push(reactive({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      sources: [],
      created_at: new Date().toISOString(),
    }))

    // Prepare assistant placeholder (reactive so mutations trigger re-renders)
    const assistantMsg = reactive({
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      sources: [],
      created_at: new Date().toISOString(),
      isStreaming: true,
    })
    messages.value.push(assistantMsg)
    streaming.value = true

    try {
      const token = localStorage.getItem('token')
      const body = { content }
      if (documentFilter) body.document_filter = documentFilter

      const response = await fetch(
        `/api/chat/${currentConversation.value.id}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(body),
        }
      )

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))

            if (event.event === 'token') {
              assistantMsg.content += event.content
            } else if (event.event === 'sources') {
              assistantMsg.sources = event.sources || []
            } else if (event.event === 'done') {
              assistantMsg.id = event.message_id
              assistantMsg.isStreaming = false
            } else if (event.event === 'error') {
              assistantMsg.content += `\n\nError: ${event.error}`
              assistantMsg.isStreaming = false
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (e) {
      assistantMsg.content = 'Connection error. Please try again.'
      assistantMsg.isStreaming = false
    } finally {
      streaming.value = false
      assistantMsg.isStreaming = false
    }
  }

  async function deleteConversation(id) {
    try {
      await api.delete(`/chat/${id}`)
      conversations.value = conversations.value.filter((c) => c.id !== id)
      if (currentConversation.value?.id === id) {
        currentConversation.value = null
        messages.value = []
      }
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to delete conversation'
    }
  }

  return {
    conversations, currentConversation, messages, loading, streaming, error,
    fetchConversations, createConversation, selectConversation,
    sendMessage, deleteConversation,
  }
})
