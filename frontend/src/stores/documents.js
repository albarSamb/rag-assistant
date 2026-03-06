import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useDocumentsStore = defineStore('documents', () => {
  const documents = ref([])
  const total = ref(0)
  const loading = ref(false)
  const uploading = ref(false)
  const error = ref(null)

  async function fetchDocuments() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/documents/')
      documents.value = data.documents
      total.value = data.total
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to load documents'
    } finally {
      loading.value = false
    }
  }

  async function uploadDocument(file) {
    uploading.value = true
    error.value = null
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      documents.value.unshift(data)
      total.value++
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Upload failed'
      return null
    } finally {
      uploading.value = false
    }
  }

  async function deleteDocument(id) {
    try {
      await api.delete(`/documents/${id}`)
      documents.value = documents.value.filter((d) => d.id !== id)
      total.value--
    } catch (e) {
      error.value = e.response?.data?.detail || 'Delete failed'
    }
  }

  async function pollDocumentStatus(id) {
    try {
      const { data } = await api.get(`/documents/${id}/status`)
      const idx = documents.value.findIndex((d) => d.id === id)
      if (idx !== -1) {
        documents.value[idx].processing_status = data.status
        documents.value[idx].chunk_count = data.chunk_count
        documents.value[idx].error_message = data.error_message
      }
      return data
    } catch {
      return null
    }
  }

  return {
    documents, total, loading, uploading, error,
    fetchDocuments, uploadDocument, deleteDocument, pollDocumentStatus,
  }
})
