<script setup>
import { ref } from 'vue'

const emit = defineEmits(['upload'])
const props = defineProps({
  uploading: { type: Boolean, default: false },
})

const dragover = ref(false)
const fileInput = ref(null)

const allowedTypes = [
  'application/pdf',
  'text/markdown',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

function handleDrop(e) {
  dragover.value = false
  const file = e.dataTransfer.files[0]
  if (file) validateAndUpload(file)
}

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) validateAndUpload(file)
  e.target.value = ''
}

function validateAndUpload(file) {
  if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|md|txt|docx)$/i)) {
    alert('Format non supporte. Utilisez PDF, Markdown, TXT ou DOCX.')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    alert('Fichier trop volumineux. Taille max : 10 Mo.')
    return
  }
  emit('upload', file)
}
</script>

<template>
  <div
    @dragover.prevent="dragover = true"
    @dragleave="dragover = false"
    @drop.prevent="handleDrop"
    @click="fileInput?.click()"
    class="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition"
    :class="dragover
      ? 'border-blue-500 bg-blue-50'
      : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'"
  >
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      accept=".pdf,.md,.txt,.docx"
      @change="handleFileSelect"
    />

    <div v-if="uploading" class="flex flex-col items-center gap-3">
      <div class="w-10 h-10 animate-spin rounded-full border-3 border-gray-300 border-t-blue-600" />
      <p class="text-sm text-gray-600">Upload en cours...</p>
    </div>

    <div v-else class="flex flex-col items-center gap-3">
      <div class="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
        <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>
      <div>
        <p class="text-sm font-medium text-gray-700">
          Glissez un fichier ici ou <span class="text-blue-600">parcourez</span>
        </p>
        <p class="text-xs text-gray-400 mt-1">PDF, Markdown, TXT, DOCX (max 10 Mo)</p>
      </div>
    </div>
  </div>
</template>
