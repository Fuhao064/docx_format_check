// frontend/src/stores/document.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v2';

export const useDocumentStore = defineStore('document', () => {
  const currentDocument = ref(null);
  const contextId = ref(null);
  const errors = ref([]);
  const isLoading = ref(false);
  const isChecking = ref(false);

  const hasDocument = computed(() => !!currentDocument.value);
  const errorCount = computed(() => errors.value.length);

  async function uploadDocument(file) {
    isLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/documents`, formData);
      const data = response.data;

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
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function prepareContext(formatId) {
    if (!currentDocument.value) return;

    try {
      const response = await axios.post(`${API_BASE}/contexts/prepare`, {
        document_id: currentDocument.value.id,
        format_id: formatId
      });

      if (response.data.success) {
        contextId.value = response.data.context_id;
        return response.data;
      }
      throw new Error(response.data.message || 'Prepare failed');
    } catch (error) {
      console.error('Prepare failed:', error);
      throw error;
    }
  }

  return {
    currentDocument,
    contextId,
    errors,
    isLoading,
    isChecking,
    hasDocument,
    errorCount,
    uploadDocument,
    prepareContext
  };
});
