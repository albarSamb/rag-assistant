<script setup>
import { ref } from 'vue'

const emit = defineEmits(['send'])
const props = defineProps({
  disabled: { type: Boolean, default: false },
})

const input = ref('')

function handleSend() {
  const text = input.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  input.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="border-t border-gray-200 bg-white px-6 py-4">
    <div class="flex items-end gap-3 max-w-4xl mx-auto">
      <textarea
        v-model="input"
        @keydown="handleKeydown"
        :disabled="disabled"
        rows="1"
        class="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition disabled:opacity-50 max-h-32"
        placeholder="Posez votre question..."
        style="field-sizing: content;"
      />
      <button
        @click="handleSend"
        :disabled="!input.trim() || disabled"
        class="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition shrink-0"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  </div>
</template>
