<template>
  <div class="home-container">
    <div class="content-wrapper">
      <div class="logo-container">
        <img src="../assets/logo.png" alt="Logo" class="logo" />
      </div>
      
      <transition name="fade">
        <button v-if="!showUploadDialog" @click="toggleUploadDialog" class="start-button">
          开始文档格式检查
        </button>
      </transition>
      
      <transition name="fade">
        <div v-if="showUploadDialog" class="upload-dialog">
          <h2>上传文件</h2>
          <div class="upload-options">
            <div class="upload-option">
              <h3>格式要求文档</h3>
              <div class="file-upload-container">
                <label for="docx-upload" class="file-upload-label">
                  <span v-if="!docxFile">选择文件</span>
                  <span v-else>{{ docxFile.name }}</span>
                </label>
                <input 
                  type="file" 
                  id="docx-upload" 
                  accept=".docx" 
                  @change="handleDocxUpload" 
                  class="file-input"
                />
              </div>
            </div>
            
            <div class="upload-option">
              <h3>格式要求JSON文件</h3>
              <div class="file-upload-container">
                <label for="json-upload" class="file-upload-label">
                  <span v-if="!jsonFile">选择文件</span>
                  <span v-else>{{ jsonFile.name }}</span>
                </label>
                <input 
                  type="file" 
                  id="json-upload" 
                  accept=".json" 
                  @change="handleJsonUpload" 
                  class="file-input"
                />
              </div>
            </div>
          </div>
          
          <div class="upload-actions">
            <button @click="toggleUploadDialog" class="cancel-button">取消</button>
            <button @click="submitFiles" class="submit-button" :disabled="!canSubmit">
              开始检查
            </button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const showUploadDialog = ref(false);
const docxFile = ref(null);
const jsonFile = ref(null);
const uploadProgress = ref(0);
const uploadError = ref('');

const toggleUploadDialog = () => {
  showUploadDialog.value = !showUploadDialog.value;
};

const handleDocxUpload = (event) => {
  const file = event.target.files[0];
  if (file && file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    docxFile.value = file;
  } else {
    alert('请上传有效的DOCX文件');
  }
};

const handleJsonUpload = (event) => {
  const file = event.target.files[0];
  if (file && file.type === 'application/json') {
    jsonFile.value = file;
  } else {
    alert('请上传有效的JSON文件');
  }
};

const canSubmit = computed(() => {
  return docxFile.value !== null || jsonFile.value !== null;
});

const submitFiles = async () => {
  if (!canSubmit.value) return;
  
  try {
    uploadError.value = '';
    uploadProgress.value = 0;
    
    const formData = new FormData();
    if (docxFile.value) {
      formData.append('docx_file', docxFile.value);
    }
    if (jsonFile.value) {
      formData.append('json_file', jsonFile.value);
    }
    
    await axios.post('/api/upload-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    });
    
    // 上传成功后跳转到对话页面
    router.push('/conversation');
  } catch (error) {
    console.error('文件上传失败:', error);
    uploadError.value = '文件上传失败，请重试';
  }
};
</script>

<style scoped>
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 800px;
  width: 100%;
  padding: 2rem;
}

.logo-container {
  margin-bottom: 3rem;
}

.logo {
  width: 180px;
  height: auto;
}

.start-button {
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 1.2rem;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s;
}

.start-button:hover {
  background-color: #3367d6;
  transform: translateY(-2px);
}

.upload-dialog {
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
}

.upload-dialog h2 {
  margin-bottom: 1.5rem;
  color: #333;
  text-align: center;
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.upload-option h3 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
  color: #555;
}

.file-upload-container {
  position: relative;
  width: 100%;
}

.file-upload-label {
  display: block;
  padding: 10px 15px;
  background-color: #f0f0f0;
  border: 1px dashed #ccc;
  border-radius: 4px;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.file-upload-label:hover {
  background-color: #e8e8e8;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.cancel-button {
  padding: 8px 16px;
  background-color: #f0f0f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button {
  padding: 8px 16px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>