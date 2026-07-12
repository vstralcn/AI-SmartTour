<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { Upload, Delete, Search, Plus, Edit } from '@element-plus/icons-vue'
import {
  createKnowledgeEntry,
  listKnowledgeDocs,
  uploadKnowledgeDoc,
  deleteKnowledgeDoc,
  testKnowledge,
  updateKnowledgeEntry,
  type KnowledgeDoc,
  type KnowledgeEntryInput,
  type KnowledgeEvidence,
} from '../../services/api'

const docs = ref<KnowledgeDoc[]>([])
const isLoading = ref(false)
const testQuestion = ref('')
const testAnswer = ref('')
const testSources = ref<string[]>([])
const testConfidence = ref(0)
const testEvidence = ref<KnowledgeEvidence[]>([])
const isTesting = ref(false)
const loadError = ref('')
const editorVisible = ref(false)
const editingId = ref('')
const editor = ref<KnowledgeEntryInput>({
  title: '',
  category: '景点介绍',
  content: '',
  kind: 'document',
  source: '',
  keywords: [],
  tags: [],
  status: 'active',
})
const keywordText = ref('')
const tagText = ref('')

async function loadDocs() {
  isLoading.value = true
  loadError.value = ''
  try {
    docs.value = await listKnowledgeDocs()
  } catch {
    docs.value = []
    loadError.value = '知识库加载失败，请检查后端和数据库状态。'
  } finally {
    isLoading.value = false
  }
}

async function handleUpload(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const doc = await uploadKnowledgeDoc(formData)
    docs.value.push(doc)
    ElMessage.success('上传成功')
  } catch {
    ElMessage.error('上传失败，请检查后端服务')
  }
}

function handleUploadChange(file: UploadFile) {
  if (file.raw) {
    handleUpload(file.raw)
  }
}

function openCreate(kind: 'document' | 'faq') {
  editingId.value = ''
  editor.value = {
    title: '',
    category: kind === 'faq' ? 'FAQ' : '景点介绍',
    content: '',
    kind,
    source: '',
    keywords: [],
    tags: [],
    status: 'active',
  }
  keywordText.value = ''
  tagText.value = ''
  editorVisible.value = true
}

function openEdit(doc: KnowledgeDoc) {
  editingId.value = doc.id
  editor.value = {
    title: doc.title,
    category: doc.category,
    content: doc.content,
    kind: doc.kind,
    source: doc.source,
    keywords: [...doc.keywords],
    tags: [...doc.tags],
    status: doc.status,
  }
  keywordText.value = doc.keywords.join('，')
  tagText.value = doc.tags.join('，')
  editorVisible.value = true
}

function splitTerms(value: string): string[] {
  return value
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

async function saveEntry() {
  if (!editor.value.title.trim() || !editor.value.content.trim()) {
    ElMessage.warning('请填写标题和知识内容')
    return
  }
  const payload: KnowledgeEntryInput = {
    ...editor.value,
    source: editor.value.source || editor.value.title,
    keywords: splitTerms(keywordText.value),
    tags: splitTerms(tagText.value),
  }
  try {
    const saved = editingId.value
      ? await updateKnowledgeEntry(editingId.value, payload)
      : await createKnowledgeEntry(payload)
    const index = docs.value.findIndex((item) => item.id === saved.id)
    if (index >= 0) {
      docs.value[index] = saved
    } else {
      docs.value.unshift(saved)
    }
    editorVisible.value = false
    ElMessage.success(editingId.value ? '知识已更新并重新索引' : '知识已创建并索引')
  } catch {
    ElMessage.error('保存失败，请检查输入和后端服务')
  }
}

async function handleDelete(doc: KnowledgeDoc) {
  try {
    await ElMessageBox.confirm(`确定删除"${doc.title}"？`, '确认删除', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteKnowledgeDoc(doc.id)
    docs.value = docs.value.filter((d) => d.id !== doc.id)
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败，请检查后端服务')
  }
}

async function handleTest() {
  if (!testQuestion.value.trim()) return
  isTesting.value = true
  testAnswer.value = ''
  testSources.value = []
  testConfidence.value = 0
  testEvidence.value = []
  try {
    const result = await testKnowledge(testQuestion.value)
    testAnswer.value = result.answer
    testSources.value = result.sources
    testConfidence.value = result.confidence
    testEvidence.value = result.evidence
  } catch {
    testAnswer.value = '测试失败，请检查后端服务后重试。'
  } finally {
    isTesting.value = false
  }
}

onMounted(loadDocs)
</script>

<template>
  <div class="knowledge-view">
    <div class="page-header">
      <h1>知识库管理</h1>
      <div class="header-actions">
        <el-button :icon="Plus" @click="openCreate('document')">新增景点知识</el-button>
        <el-button :icon="Plus" @click="openCreate('faq')">新增 FAQ</el-button>
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          accept=".pdf,.txt,.docx,.md"
          :on-change="handleUploadChange"
        >
          <el-button type="primary" :icon="Upload">上传文档</el-button>
        </el-upload>
      </div>
    </div>
    <el-alert v-if="loadError" :title="loadError" type="error" show-icon />

    <div class="content-grid">
      <div class="docs-section">
        <el-table :data="docs" v-loading="isLoading" stripe>
          <el-table-column prop="title" label="文档标题" min-width="200" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="类型" width="90">
            <template #default="{ row }">
              <el-tag :type="row.kind === 'faq' ? 'warning' : 'info'" size="small">
                {{ row.kind === 'faq' ? 'FAQ' : '文档' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="upload_time" label="上传时间" width="180" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '已启用' : '已归档' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button
                type="primary"
                :icon="Edit"
                size="small"
                link
                @click="openEdit(row)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                :icon="Delete"
                size="small"
                link
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="test-section">
        <h3>知识库测试</h3>
        <p class="test-hint">输入问题测试知识库问答效果</p>
        <div class="test-input">
          <el-input
            v-model="testQuestion"
            placeholder="例如：景区的开放时间是什么？"
            @keyup.enter="handleTest"
          />
          <el-button
            type="primary"
            :icon="Search"
            :loading="isTesting"
            @click="handleTest"
          >
            测试
          </el-button>
        </div>
        <div v-if="testAnswer" class="test-result">
          <div class="result-answer">
            <div class="answer-header">
              <h4>回答：</h4>
              <el-tag :type="testConfidence >= 0.6 ? 'success' : 'warning'" size="small">
                置信度 {{ Math.round(testConfidence * 100) }}%
              </el-tag>
            </div>
            <p>{{ testAnswer }}</p>
          </div>
          <div class="result-sources" v-if="testSources.length">
            <h4>参考来源：</h4>
            <el-tag v-for="s in testSources" :key="s" size="small" class="source-tag">
              {{ s }}
            </el-tag>
          </div>
          <div class="evidence-list" v-if="testEvidence.length">
            <h4>证据片段：</h4>
            <div v-for="item in testEvidence" :key="`${item.source}-${item.title}`" class="evidence-item">
              <div class="evidence-meta">
                <strong>{{ item.title }}</strong>
                <span>{{ Math.round(item.score * 100) }}%</span>
              </div>
              <p>{{ item.excerpt }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="editorVisible"
      :title="editingId ? '编辑知识条目' : '新增知识条目'"
      width="620px"
    >
      <el-form label-position="top">
        <div class="form-row">
          <el-form-item label="类型">
            <el-select v-model="editor.kind">
              <el-option label="景点/业务知识" value="document" />
              <el-option label="常见问题 FAQ" value="faq" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model="editor.category" />
          </el-form-item>
        </div>
        <el-form-item label="标题">
          <el-input v-model="editor.title" />
        </el-form-item>
        <el-form-item label="知识内容 / FAQ 答案">
          <el-input v-model="editor.content" type="textarea" :rows="7" />
        </el-form-item>
        <el-form-item label="FAQ 匹配词（逗号分隔）">
          <el-input v-model="keywordText" placeholder="例如：几点开门，开放时间" />
        </el-form-item>
        <el-form-item label="检索标签（逗号分隔）">
          <el-input v-model="tagText" placeholder="例如：古建筑，历史文化" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="editor.source" placeholder="留空时使用标题" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editorVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEntry">保存并重新索引</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.knowledge-view {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-row :deep(.el-select) {
  width: 100%;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.answer-header,
.evidence-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.evidence-list {
  margin-top: 16px;
}

.evidence-item {
  margin-top: 8px;
  padding: 10px 12px;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  background: #eff6ff;
}

.evidence-meta {
  color: #1d4ed8;
  font-size: 13px;
}

.evidence-item p {
  margin: 6px 0 0;
  color: #475569;
  line-height: 1.6;
}

.docs-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.test-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.test-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.test-hint {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 12px;
}

.test-input {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.test-result {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
}

.result-answer h4,
.result-sources h4 {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.result-answer p {
  font-size: 14px;
  color: #1f2937;
  line-height: 1.6;
  margin-bottom: 12px;
}

.source-tag {
  margin-right: 8px;
}
</style>
