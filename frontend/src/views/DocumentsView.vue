<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '../stores/documents'
import UploadZone from '../components/documents/UploadZone.vue'
import DocumentCard from '../components/documents/DocumentCard.vue'
import LoadingSpinner from '../components/common/LoadingSpinner.vue'

const docs = useDocumentsStore()

onMounted(() => {
  docs.fetchDocuments()
})

async function handleUpload(file) {
  const doc = await docs.uploadDocument(file)
  if (doc) {
    pollStatus(doc.id)
  }
}

function pollStatus(id) {
  const interval = setInterval(async () => {
    const status = await docs.pollDocumentStatus(id)
    if (!status || status.status === 'completed' || status.status === 'failed') {
      clearInterval(interval)
    }
  }, 2000)
}

function handleDelete(id) {
  if (confirm('Supprimer ce document et tous ses chunks ?')) {
    docs.deleteDocument(id)
  }
}
</script>

<template>
  <div class="flex-1 overflow-y-auto">
    <div class="max-w-4xl mx-auto px-6 py-8">
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900">Documents</h1>
        <p class="text-gray-500 mt-1">Uploadez vos fichiers pour les interroger via le chat</p>
      </div>

      <!-- Upload Zone -->
      <UploadZone @upload="handleUpload" :uploading="docs.uploading" />

      <!-- Error -->
      <div v-if="docs.error" class="mt-4 bg-red-50 text-red-600 text-sm rounded-lg p-3">
        {{ docs.error }}
      </div>

      <!-- Loading -->
      <div v-if="docs.loading" class="mt-8 flex justify-center">
        <LoadingSpinner size="lg" />
      </div>

      <!-- Documents list -->
      <div class="mt-8">
        <h2 class="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
          {{ docs.total }} document{{ docs.total !== 1 ? 's' : '' }}
        </h2>
        <div class="space-y-3">
          <DocumentCard
            v-for="doc in docs.documents"
            :key="doc.id"
            :document="doc"
            @delete="handleDelete(doc.id)"
          />
        </div>
        <p v-if="!docs.loading && docs.documents.length === 0" class="text-gray-400 text-center py-12">
          Aucun document. Commencez par uploader un fichier.
        </p>
      </div>
    </div>
  </div>
</template>
