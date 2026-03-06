<script setup>
import { ref } from 'vue'

const props = defineProps({
  source: { type: Object, required: true },
  index: { type: Number, required: true },
})

const expanded = ref(false)
</script>

<template>
  <div
    @click="expanded = !expanded"
    class="cursor-pointer border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs bg-gray-50 hover:bg-gray-100 transition"
    :class="{ 'w-full': expanded }"
  >
    <div class="flex items-center gap-1.5">
      <span class="bg-blue-100 text-blue-700 rounded px-1.5 py-0.5 font-medium">{{ index }}</span>
      <span class="text-gray-600 truncate">{{ source.metadata?.filename || 'Source' }}</span>
      <span v-if="source.score" class="text-gray-400 ml-auto">{{ (source.score * 100).toFixed(0) }}%</span>
    </div>
    <div v-if="expanded" class="mt-2 text-gray-600 text-xs leading-relaxed border-t border-gray-200 pt-2">
      {{ source.content }}
    </div>
  </div>
</template>
