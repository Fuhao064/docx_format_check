// frontend/src/stores/document.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { documentsAPI, contextsAPI } from '@/api/client_v2.js';

export const useDocumentStore = defineStore('document', () => {
  const currentDocument = ref(null);
  const contextId = ref(null);
  const errors = ref([]);
  const isLoading = ref(false);

  const hasDocument = computed(() => !!currentDocument.value);
  const errorCount = computed(() => errors.value.length);

  async function uploadDocument(file) {
    isLoading.value = true;
    try {
      const data = await documentsAPI.upload(file);

      if (data.success) {
        currentDocument.value = {
          id: data.document_id,
          name: data.filename,
          path: data.file_path
        };
        return data;
      }
      throw new Error(data.message || 'Upload failed');
    } catch (error) {
      console.error('Upload failed:', error);
      errors.value.push({ message: error.message, timestamp: Date.now() });
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function prepareContext(formatId) {
    if (!currentDocument.value) {
      throw new Error('No document uploaded');
    }

    isLoading.value = true;
    try {
      const data = await contextsAPI.prepare(currentDocument.value.id, formatId);

      if (data.success) {
        contextId.value = data.context_id;
        return data;
      }
      throw new Error(data.message || 'Prepare failed');
    } catch (error) {
      console.error('Prepare failed:', error);
      errors.value.push({ message: error.message, timestamp: Date.now() });
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    currentDocument,
    contextId,
    errors,
    isLoading,
    hasDocument,
    errorCount,
    uploadDocument,
    prepareContext
  };
});
