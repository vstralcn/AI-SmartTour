<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  activateAvatar,
  deleteAvatar,
  listAvatars,
  saveAvatarConfig,
  type AvatarConfig,
} from '../../services/api'

const avatars = ref<AvatarConfig[]>([])
const loadError = ref('')

function blankAvatar(): AvatarConfig {
  return {
    id: '',
    name: '',
    appearance: { image_url: '/avatars/xiaozhi.png', style: '现代国风' },
    voice_config: { voice_id: 'female-1', speed: 1.0, pitch: 1.0 },
    personality: '热情开朗，知识渊博',
    gender: '女',
    clothing: '现代导游服',
    speaking_style: '亲切自然',
    is_active: false,
  }
}

const currentConfig = ref<AvatarConfig>({
  ...blankAvatar(),
  name: '',
})

const styleOptions = ['现代国风', '古典汉服', '民族特色', '休闲', '正式']
const clothingOptions = ['现代导游服', '传统汉服', '节日服装', '民族服装']
const speakingStyleOptions = ['亲切活泼', '沉稳叙事', '儿童友好', '专业精炼']
const voiceOptions = [
  { id: 'female-1', label: '温柔女声' },
  { id: 'female-2', label: '活泼女声' },
  { id: 'male-1', label: '稳重男声' },
  { id: 'male-2', label: '磁性男声' },
]

async function loadAvatars() {
  loadError.value = ''
  try {
    avatars.value = await listAvatars()
  } catch {
    avatars.value = []
    loadError.value = '数字人配置加载失败，请检查后端和数据库状态。'
  }
}

async function handleSave() {
  if (!currentConfig.value.name.trim()) {
    ElMessage.warning('请输入数字人名称')
    return
  }
  try {
    const saved = await saveAvatarConfig(currentConfig.value)
    const idx = avatars.value.findIndex((a) => a.id === saved.id)
    if (idx >= 0) {
      avatars.value[idx] = saved
    } else {
      avatars.value.push(saved)
    }
    currentConfig.value = {
      ...saved,
      appearance: { ...saved.appearance },
      voice_config: { ...saved.voice_config },
    }
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.error('保存失败，请检查后端服务')
  }
}

async function handleActivate(avatar: AvatarConfig) {
  try {
    await activateAvatar(avatar.id)
  } catch {
    ElMessage.error('激活失败，请检查后端服务')
    return
  }
  avatars.value.forEach((a) => (a.is_active = a.id === avatar.id))
  ElMessage.success(`已激活"${avatar.name}"`)
}

function editAvatar(avatar: AvatarConfig) {
  currentConfig.value = {
    ...avatar,
    appearance: { ...avatar.appearance },
    voice_config: { ...avatar.voice_config },
  }
}

function createAvatar() {
  currentConfig.value = blankAvatar()
}

async function handleDelete(avatar: AvatarConfig) {
  try {
    await ElMessageBox.confirm(`确定删除“${avatar.name}”？`, '确认删除', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteAvatar(avatar.id)
    avatars.value = avatars.value.filter((item) => item.id !== avatar.id)
    if (currentConfig.value.id === avatar.id) {
      createAvatar()
    }
    ElMessage.success('数字人已删除')
  } catch {
    ElMessage.error('删除失败：当前使用中的数字人不能删除')
  }
}

onMounted(loadAvatars)
</script>

<template>
  <div class="avatar-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">数字人形象管理</h1>
        <p>激活后游客端将立即使用对应形象、音色和讲解风格</p>
      </div>
      <el-button type="primary" @click="createAvatar">创建角色</el-button>
    </div>
    <el-alert v-if="loadError" :title="loadError" type="error" show-icon />

    <div class="avatar-grid">
      <div class="avatar-list">
        <h3>已有形象</h3>
        <div class="avatar-cards">
          <div
            v-for="avatar in avatars"
            :key="avatar.id"
            class="avatar-card"
            :class="{ active: avatar.is_active }"
          >
            <div class="avatar-preview">
              <img :src="avatar.appearance.image_url" :alt="avatar.name" />
            </div>
            <div class="avatar-info">
              <h4>{{ avatar.name }}</h4>
              <p>{{ avatar.appearance.style }} | {{ voiceOptions.find(v => v.id === avatar.voice_config.voice_id)?.label || avatar.voice_config.voice_id }}</p>
              <p>{{ avatar.gender }} · {{ avatar.clothing }} · {{ avatar.speaking_style }}</p>
              <p class="personality">{{ avatar.personality }}</p>
            </div>
            <div class="avatar-actions">
              <el-button size="small" @click="editAvatar(avatar)">编辑</el-button>
              <el-button
                size="small"
                :type="avatar.is_active ? 'success' : 'primary'"
                @click="handleActivate(avatar)"
                :disabled="avatar.is_active"
              >
                {{ avatar.is_active ? '当前使用' : '激活' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                :disabled="avatar.is_active"
                @click="handleDelete(avatar)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="avatar-editor">
        <h3>形象配置</h3>
        <el-form label-position="top">
          <el-form-item label="名称">
            <el-input v-model="currentConfig.name" placeholder="数字人名称" />
          </el-form-item>

          <el-form-item label="形象图片">
            <el-input v-model="currentConfig.appearance.image_url" placeholder="/avatars/name.png" />
          </el-form-item>

          <el-form-item label="性别">
            <el-radio-group v-model="currentConfig.gender">
              <el-radio-button label="女" />
              <el-radio-button label="男" />
              <el-radio-button label="中性" />
            </el-radio-group>
          </el-form-item>

          <el-form-item label="服装风格">
            <el-select v-model="currentConfig.appearance.style" style="width: 100%">
              <el-option v-for="s in styleOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>

          <el-form-item label="服装">
            <el-select v-model="currentConfig.clothing" style="width: 100%">
              <el-option v-for="item in clothingOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <el-form-item label="讲解风格">
            <el-select v-model="currentConfig.speaking_style" style="width: 100%">
              <el-option
                v-for="item in speakingStyleOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="语音音色">
            <el-select v-model="currentConfig.voice_config.voice_id" style="width: 100%">
              <el-option
                v-for="v in voiceOptions"
                :key="v.id"
                :label="v.label"
                :value="v.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="语速">
            <el-slider
              v-model="currentConfig.voice_config.speed"
              :min="0.5"
              :max="2.0"
              :step="0.1"
              show-stops
            />
          </el-form-item>

          <el-form-item label="语调">
            <el-slider
              v-model="currentConfig.voice_config.pitch"
              :min="0.5"
              :max="2.0"
              :step="0.1"
              show-stops
            />
          </el-form-item>

          <el-form-item label="性格设定">
            <el-input
              v-model="currentConfig.personality"
              type="textarea"
              :rows="3"
              placeholder="描述数字人的性格特征..."
            />
          </el-form-item>

          <el-button type="primary" @click="handleSave" style="width: 100%">
            保存配置
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.avatar-view {
  padding: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header p {
  color: #6b7280;
  font-size: 13px;
}

.avatar-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

.avatar-list h3,
.avatar-editor h3 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
}

.avatar-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.avatar-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 2px solid transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: border-color 0.2s;
}

.avatar-card.active {
  border-color: #4f46e5;
}

.avatar-preview {
  flex-shrink: 0;
}

.avatar-preview img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e0e7ff;
}

.avatar-info {
  flex: 1;
  min-width: 0;
}

.avatar-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.avatar-info p {
  font-size: 13px;
  color: #6b7280;
}

.personality {
  margin-top: 4px;
  font-size: 12px !important;
  color: #9ca3af !important;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.avatar-editor {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: fit-content;
}
</style>
