<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import AppSidebar from '../components/common/AppSidebar.vue'

const auth = useAuthStore()
const chat = useChatStore()

onMounted(() => {
  chat.fetchConversations()
})
</script>

<template>
  <div class="h-screen flex overflow-hidden bg-gray-50">
    <AppSidebar />
    <main class="flex-1 flex flex-col overflow-hidden">
      <router-view />
    </main>
  </div>
</template>
