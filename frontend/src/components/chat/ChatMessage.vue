<script setup>
import { computed } from 'vue'
import SourceCard from './SourceCard.vue'

const props = defineProps({
  message: { type: Object, required: true },
})

const isUser = computed(() => props.message.role === 'user')
const hasSources = computed(() => props.message.sources?.length > 0)
</script>

<template>
  <div class="flex gap-3" :class="isUser ? 'justify-end' : 'justify-start'">
    <!-- Avatar -->
    <div
      v-if="!isUser"
      class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-blue-600 text-white text-sm font-medium"
    >
      AI
    </div>

    <div class="max-w-[75%] space-y-2">
      <!-- Message bubble -->
      <div
        class="rounded-2xl px-4 py-3 text-sm leading-relaxed"
        :class="isUser
          ? 'bg-blue-600 text-white rounded-br-md'
          : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md shadow-sm'"
      >
        <div
          :class="{ 'streaming-cursor': message.isStreaming }"
          style="white-space: pre-wrap;"
        >{{ message.content || '...' }}</div>
      </div>

      <!-- Sources -->
      <div v-if="hasSources && !isUser" class="space-y-1">
        <p class="text-xs text-gray-500 font-medium">Sources :</p>
        <div class="flex flex-wrap gap-1.5">
          <SourceCard
            v-for="(source, i) in message.sources"
            :key="i"
            :source="source"
            :index="i + 1"
          />
        </div>
      </div>
    </div>

    <!-- User avatar -->
    <div
      v-if="isUser"
      class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-gray-700 text-white text-sm font-medium"
    >
      U
    </div>
  </div>
</template>
