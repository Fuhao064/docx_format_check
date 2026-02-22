<template>
  <div class="fix-report">
    <div class="report-header">
      <h3>自动修复报告</h3>
      <div v-if="report" class="report-summary">
        <span class="summary-item success">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 13l4 4L19 7"></path>
          </svg>
          成功: {{ report.total_fixed || 0 }}
        </span>
        <span class="summary-item warning">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          跳过: {{ report.total_skipped || 0 }}
        </span>
        <span class="summary-item error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          失败: {{ report.total_failed || 0 }}
        </span>
      </div>
    </div>

    <div v-if="report && report.actions && report.actions.length" class="report-content">
      <div v-for="(action, index) in report.actions" :key="index"
           class="action-item"
           :class="action.status">
        <div class="action-status">
          <span class="status-badge" :class="action.status">
            {{ getStatusLabel(action.status) }}
          </span>
        </div>
        <div class="action-details">
          <div class="action-title">{{ action.description || action.error_type || '修复操作' }}</div>
          <div v-if="action.location" class="action-location">
            <small>位置: {{ action.location }}</small>
          </div>
          <div v-if="action.message" class="action-message">
            <small>{{ action.message }}</small>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="report" class="no-actions">
      没有修复记录
    </div>

    <div v-if="repairId && showDownloadButton" class="report-footer">
      <button @click="downloadFixedDocument"
              class="download-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        下载修复后文档
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  report: {
    type: Object,
    default: null
  },
  repairId: {
    type: String,
    default: ''
  },
  showDownloadButton: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['download-start', 'download-complete', 'download-error'])

function getStatusLabel(status) {
  const labels = {
    'fixed': '已修复',
    'skipped': '已跳过',
    'failed': '失败',
    'pending': '等待中'
  }
  return labels[status] || status
}

async function downloadFixedDocument() {
  if (!props.repairId) {
    return
  }

  emit('download-start')

  try {
    const response = await axios.get(`/api/v2/repairs/${props.repairId}/document`, {
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    const disposition = response.headers['content-disposition']
    let filename = 'fixed_document.docx'
    if (disposition) {
      const filenameMatch = disposition.match(/filename="?([^";]+)"?/i)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    emit('download-complete')
  } catch (error) {
    emit('download-error', error)
    throw error
  }
}
</script>

<style scoped>
.fix-report {
  padding: 20px;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: 12px;
}

.report-header {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid hsl(var(--border));
}

.report-header h3 {
  margin: 0;
  font-size: 18px;
}

.report-summary {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.summary-item.success {
  background: hsl(var(--success) / 0.15);
  color: hsl(var(--success));
}

.summary-item.warning {
  background: hsl(var(--warning) / 0.15);
  color: hsl(var(--warning));
}

.summary-item.error {
  background: hsl(var(--destructive) / 0.15);
  color: hsl(var(--destructive));
}

.report-content {
  max-height: 400px;
  overflow-y: auto;
}

.action-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: hsl(var(--muted) / 0.1);
  border-left: 3px solid hsl(var(--muted-foreground));
}

.action-item.fixed {
  background: hsl(var(--success) / 0.1);
  border-left-color: hsl(var(--success));
}

.action-item.skipped {
  background: hsl(var(--warning) / 0.1);
  border-left-color: hsl(var(--warning));
}

.action-item.failed {
  background: hsl(var(--destructive) / 0.1);
  border-left-color: hsl(var(--destructive));
}

.action-status {
  flex-shrink: 0;
}

.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.fixed {
  background: hsl(var(--success) / 0.2);
  color: hsl(var(--success));
}

.status-badge.skipped {
  background: hsl(var(--warning) / 0.2);
  color: hsl(var(--warning));
}

.status-badge.failed {
  background: hsl(var(--destructive) / 0.2);
  color: hsl(var(--destructive));
}

.action-details {
  flex: 1;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.action-location,
.action-message {
  color: hsl(var(--muted-foreground));
  line-height: 1.4;
}

.no-actions {
  text-align: center;
  padding: 40px;
  color: hsl(var(--muted-foreground));
}

.report-footer {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid hsl(var(--border));
}

.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 24px;
  border: none;
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.download-btn:hover {
  background: hsl(var(--primary) / 0.9);
}
</style>
