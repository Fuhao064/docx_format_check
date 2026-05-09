// frontend/src/api/client_v2.js
import axios from 'axios';

const API_BASE = '/api/v2';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
client.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default client;

// 文档 API
export const documentsAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 格式 API
export const formatsAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/formats', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 上下文 API
export const contextsAPI = {
  prepare: (documentId, formatId) => {
    return client.post('/contexts/prepare', {
      document_id: documentId,
      format_id: formatId
    });
  }
};
