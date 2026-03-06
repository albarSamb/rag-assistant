<script setup>
defineProps({
  size: { type: String, default: 'md' },
})
</script>

<template>
  <div class="flex items-center justify-center">
    <div
      class="animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
      :class="{
        'w-4 h-4': size === 'sm',
        'w-6 h-6': size === 'md',
        'w-10 h-10': size === 'lg',
      }"
    />
  </div>
</template>
