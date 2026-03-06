<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useChatStore } from '../../stores/chat'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const chat = useChatStore()
const collapsed = ref(false)

async function newConversation() {
  const conv = await chat.createConversation('Nouvelle conversation')
  if (conv) router.push(`/chat/${conv.id}`)
}

function selectConversation(id) {
  router.push(`/chat/${id}`)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function deleteConv(id, e) {
  e.stopPropagation()
  if (confirm('Supprimer cette conversation ?')) {
    chat.deleteConversation(id)
  }
}
</script>

<template>
  <aside
    class="bg-gray-900 text-white flex flex-col transition-all duration-200"
    :class="collapsed ? 'w-16' : 'w-72'"
  >
    <!-- Header -->
    <div class="p-4 flex items-center justify-between border-b border-gray-700">
      <span v-if="!collapsed" class="font-bold text-lg">DocuBot</span>
      <button
        @click="collapsed = !collapsed"
        class="p-1.5 rounded-lg hover:bg-gray-700 transition text-gray-400"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </div>

    <!-- New Chat button -->
    <div class="p-3">
      <button
        @click="newConversation"
        class="w-full flex items-center gap-2 px-3 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span v-if="!collapsed">Nouvelle conversation</span>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="px-3 space-y-1">
      <router-link
        to="/chat"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition"
        :class="route.path.startsWith('/chat') ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <span v-if="!collapsed">Chat</span>
      </router-link>

      <router-link
        to="/documents"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition"
        :class="route.path === '/documents' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span v-if="!collapsed">Documents</span>
      </router-link>
    </nav>

    <!-- Conversations list -->
    <div v-if="!collapsed" class="flex-1 overflow-y-auto px-3 mt-4">
      <p class="text-xs text-gray-500 uppercase tracking-wide px-3 mb-2">Conversations</p>
      <div
        v-for="conv in chat.conversations"
        :key="conv.id"
        @click="selectConversation(conv.id)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer group transition"
        :class="chat.currentConversation?.id === conv.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
      >
        <span class="truncate">{{ conv.title || 'Sans titre' }}</span>
        <button
          @click="deleteConv(conv.id, $event)"
          class="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      <p v-if="chat.conversations.length === 0" class="text-gray-500 text-sm text-center mt-4">
        Aucune conversation
      </p>
    </div>

    <!-- User section -->
    <div class="p-3 border-t border-gray-700">
      <div class="flex items-center gap-3 px-3 py-2">
        <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-medium shrink-0">
          {{ auth.user?.full_name?.[0]?.toUpperCase() || '?' }}
        </div>
        <div v-if="!collapsed" class="flex-1 min-w-0">
          <p class="text-sm font-medium truncate">{{ auth.user?.full_name || 'User' }}</p>
          <p class="text-xs text-gray-400 truncate">{{ auth.user?.email }}</p>
        </div>
        <button
          v-if="!collapsed"
          @click="handleLogout"
          class="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition"
          title="Deconnexion"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>
