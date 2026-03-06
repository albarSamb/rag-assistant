<script setup>
import { computed } from 'vue'

const props = defineProps({
  document: { type: Object, required: true },
})
const emit = defineEmits(['delete'])

const statusConfig = computed(() => {
  const s = props.document.processing_status
  if (s === 'completed') return { label: 'Traite', color: 'bg-green-100 text-green-700' }
  if (s === 'processing') return { label: 'En cours...', color: 'bg-yellow-100 text-yellow-700' }
  if (s === 'failed') return { label: 'Erreur', color: 'bg-red-100 text-red-700' }
  return { label: 'En attente', color: 'bg-gray-100 text-gray-600' }
})

const fileSize = computed(() => {
  const bytes = props.document.file_size
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
})

const fileIcon = computed(() => {
  const mime = props.document.mime_type
  if (mime === 'application/pdf') return { bg: 'bg-red-100', text: 'text-red-600', label: 'PDF' }
  if (mime === 'text/markdown') return { bg: 'bg-purple-100', text: 'text-purple-600', label: 'MD' }
  if (mime?.includes('word')) return { bg: 'bg-blue-100', text: 'text-blue-600', label: 'DOC' }
  return { bg: 'bg-gray-100', text: 'text-gray-600', label: 'TXT' }
})
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-4 hover:shadow-sm transition">
    <!-- File type icon -->
    <div
      class="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
      :class="[fileIcon.bg, fileIcon.text]"
    >
      {{ fileIcon.label }}
    </div>

    <!-- Info -->
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium text-gray-900 truncate">{{ document.original_name }}</p>
      <div class="flex items-center gap-3 mt-0.5">
        <span class="text-xs text-gray-400">{{ fileSize }}</span>
        <span v-if="document.chunk_count" class="text-xs text-gray-400">{{ document.chunk_count }} chunks</span>
      </div>
    </div>

    <!-- Status badge -->
    <span
      class="text-xs font-medium px-2.5 py-1 rounded-full shrink-0"
      :class="statusConfig.color"
    >
      {{ statusConfig.label }}
    </span>

    <!-- Error message -->
    <span v-if="document.error_message" class="text-xs text-red-500 max-w-32 truncate" :title="document.error_message">
      {{ document.error_message }}
    </span>

    <!-- Delete button -->
    <button
      @click="emit('delete')"
      class="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition shrink-0"
      title="Supprimer"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
  </div>
</template>
