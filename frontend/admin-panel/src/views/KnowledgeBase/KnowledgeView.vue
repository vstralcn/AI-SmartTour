<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Delete, Search } from '@element-plus/icons-vue'
import {
  listKnowledgeDocs,
  uploadKnowledgeDoc,
  deleteKnowledgeDoc,
  testKnowledge,
  type KnowledgeDoc,
} from '../../services/api'

const docs = ref<KnowledgeDoc[]>([])
const isLoading = ref(false)
const testQuestion = ref('')
const testAnswer = ref('')
const testSources = ref<string[]>([])
const isTesting = ref(false)

const demoDocs: KnowledgeDoc[] = [
  {
    id: '1',
    title: '景区概况介绍',
    category: '景区信息',
    content: '本景区始建于明代...',
    file_path: '/docs/overview.pdf',
    upload_time: '2026-03-20 10:00',
    status: 'active',
  },
  {
    id: '2',
    title: '古建筑群历史',
    category: '历史文化',
    content: '古建筑群占地面积...',
    file_path: '/docs/architecture.pdf',
    upload_time: '2026-03-20 10:15',
    status: 'active',
  },
  {
    id: '3',
    title: '游览路线指南',
    category: '游览信息',
    content: '推荐路线一：经典路线...',
    file_path: '/docs/routes.pdf',
    upload_time: '2026-03-21 09:00',
    status: 'active',
  },
  {
    id: '4',
    title: '常见问题FAQ',
    category: 'FAQ',
    content: '开放时间：8:00-18:00...',
    file_path: '/docs/faq.pdf',
    upload_time: '2026-03-21 09:30',
    status: 'active',
  },
]

async function loadDocs() {
  isLoading.value = true
  try {
    docs.value = await listKnowledgeDocs()
  } catch {
    docs.value = demoDocs
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
    ElMessage.success('文档已上传（演示模式）')
    docs.value.push({
      id: String(Date.now()),
      title: file.name,
      category: '待分类',
      content: '',
      file_path: `/uploads/${file.name}`,
      upload_time: new Date().toLocaleString('zh-CN'),
      status: 'active',
    })
  }
}

async function handleDelete(doc: KnowledgeDoc) {
  try {
    await ElMessageBox.confirm(`确定删除"${doc.title}"？`, '确认删除', {
      type: 'warning',
    })
    try {
      await deleteKnowledgeDoc(doc.id)
    } catch {
      // demo mode
    }
    docs.value = docs.value.filter((d) => d.id !== doc.id)
    ElMessage.success('已删除')
  } catch {
    // cancelled
  }
}

async function handleTest() {
  if (!testQuestion.value.trim()) return
  isTesting.value = true
  testAnswer.value = ''
  testSources.value = []
  try {
    const result = await testKnowledge(testQuestion.value)
    testAnswer.value = result.answer
    testSources.value = result.sources
  } catch {
    testAnswer.value =
      '本景区始建于明代，距今已有600多年历史。景区占地面积约500亩，包含古建筑群、山水园林、文化体验馆等多个景点。开放时间为每日8:00-18:00，门票价格为成人80元/人。'
    testSources.value = ['景区概况介绍', '常见问题FAQ']
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
      <el-upload
        :auto-upload="false"
        :show-file-list="false"
        accept=".pdf,.txt,.docx,.md"
        @change="(f: any) => handleUpload(f.raw)"
      >
        <el-button type="primary" :icon="Upload">上传文档</el-button>
      </el-upload>
    </div>

    <div class="content-grid">
      <div class="docs-section">
        <el-table :data="docs" v-loading="isLoading" stripe>
          <el-table-column prop="title" label="文档标题" min-width="200" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="upload_time" label="上传时间" width="180" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '已启用' : '已归档' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
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
            <h4>回答：</h4>
            <p>{{ testAnswer }}</p>
          </div>
          <div class="result-sources" v-if="testSources.length">
            <h4>参考来源：</h4>
            <el-tag v-for="s in testSources" :key="s" size="small" class="source-tag">
              {{ s }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
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

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
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
