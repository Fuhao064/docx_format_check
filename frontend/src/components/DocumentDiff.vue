<template>
  <div class="document-diff">
    <div class="diff-header">
      <h3>文档对比</h3>
      <div class="diff-stats" v-if="statistics">
        <span class="stat added">新增: {{ statistics.added }}</span>
        <span class="stat removed">删除: {{ statistics.removed }}</span>
        <span class="stat modified">修改: {{ statistics.modified }}</span>
        <span class="stat format-changed">格式: {{ statistics.format_changed }}</span>
      </div>
    </div>

    <div class="diff-content" v-if="changes && changes.length">
      <div v-for="(change, index) in changes" :key="index"
           class="diff-paragraph"
           :class="change.change_type">
        <div class="para-header">
          <span class="para-index">段落 {{ change.index }}</span>
          <span class="para-type">{{ getChangeTypeLabel(change.change_type) }}</span>
        </div>
        <div class="para-content" v-if="change.change_type === 'added'">
          {{ change.new_content }}
        </div>
        <div class="para-content" v-else-if="change.change_type === 'removed'">
          {{ change.old_content }}
        </div>
        <div class="para-content" v-else>
          <div v-if="change.content_diff" class="content-diff">
            <span v-for="(diff, i) in change.content_diff" :key="i"
                  :class="'diff-word-' + diff.type">
              {{ diff.content }}
            </span>
          </div>
          <div v-else>
            {{ change.new_content }}
          </div>
          <div v-if="change.format_changes && change.format_changes.length" class="format-changes">
            <small>格式变化: {{ change.format_changes.join(', ') }}</small>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="no-changes">
      没有变化数据
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  statistics: {
    type: Object,
    default: null
  },
  changes: {
    type: Array,
    default: () => []
  }
})

function getChangeTypeLabel(type) {
  const labels = {
    'added': '新增',
    'removed': '删除',
    'modified': '修改',
    'format_changed': '格式变化',
    'unchanged': '未变化'
  }
  return labels[type] || type
}
</script>

<style scoped>
.document-diff {
  padding: 20px;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: 12px;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid hsl(var(--border));
}

.diff-header h3 {
  margin: 0;
  font-size: 18px;
}

.diff-stats {
  display: flex;
  gap: 15px;
}

.stat {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.stat.added {
  background: hsl(var(--success) / 0.15);
  color: hsl(var(--success));
}

.stat.removed {
  background: hsl(var(--destructive) / 0.15);
  color: hsl(var(--destructive));
}

.stat.modified {
  background: hsl(var(--warning) / 0.15);
  color: hsl(var(--warning));
}

.stat.format-changed {
  background: hsl(var(--info) / 0.15);
  color: hsl(var(--info));
}

.diff-content {
  max-height: 500px;
  overflow-y: auto;
}

.diff-paragraph {
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 8px;
  border-left: 3px solid transparent;
}

.diff-paragraph.added {
  background: hsl(var(--success) / 0.1);
  border-left-color: hsl(var(--success));
}

.diff-paragraph.removed {
  background: hsl(var(--destructive) / 0.1);
  border-left-color: hsl(var(--destructive));
}

.diff-paragraph.modified {
  background: hsl(var(--warning) / 0.1);
  border-left-color: hsl(var(--warning));
}

.diff-paragraph.format_changed {
  background: hsl(var(--info) / 0.1);
  border-left-color: hsl(var(--info));
}

.diff-paragraph.unchanged {
  background: hsl(var(--muted) / 0.1);
  border-left-color: hsl(var(--muted-foreground));
}

.para-header {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 12px;
}

.para-index {
  font-weight: 600;
  color: hsl(var(--muted-foreground));
}

.para-type {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
}

.para-content {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
}

.format-changes {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed hsl(var(--border));
  color: hsl(var(--muted-foreground));
}

.diff-word-added {
  background: hsl(var(--success) / 0.3);
  padding: 2px 4px;
  border-radius: 3px;
}

.diff-word-removed {
  background: hsl(var(--destructive) / 0.3);
  padding: 2px 4px;
  border-radius: 3px;
  text-decoration: line-through;
}

.no-changes {
  text-align: center;
  padding: 40px;
  color: hsl(var(--muted-foreground));
}
</style>
