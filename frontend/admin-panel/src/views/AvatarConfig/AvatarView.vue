<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listAvatars, saveAvatarConfig, activateAvatar, type AvatarConfig } from '../../services/api'

const avatars = ref<AvatarConfig[]>([])
const currentConfig = ref<Partial<AvatarConfig>>({
  name: '',
  appearance: { image_url: '', style: '现代' },
  voice_config: { voice_id: 'female-1', speed: 1.0, pitch: 1.0 },
  personality: '热情开朗，知识渊博',
})

const styleOptions = ['现代', '古典汉服', '民族特色', '休闲', '正式']
const voiceOptions = [
  { id: 'female-1', label: '温柔女声' },
  { id: 'female-2', label: '活泼女声' },
  { id: 'male-1', label: '稳重男声' },
  { id: 'male-2', label: '磁性男声' },
]

const demoAvatars: AvatarConfig[] = [
  {
    id: '1',
    name: '小智',
    appearance: { image_url: '/avatars/xiazhi.png', style: '现代' },
    voice_config: { voice_id: 'female-1', speed: 1.0, pitch: 1.0 },
    personality: '热情开朗，善于讲故事',
    is_active: true,
  },
  {
    id: '2',
    name: '文渊',
    appearance: { image_url: '/avatars/wenyuan.png', style: '古典汉服' },
    voice_config: { voice_id: 'male-1', speed: 0.9, pitch: 0.95 },
    personality: '博学稳重，擅长历史文化讲解',
    is_active: false,
  },
]

async function loadAvatars() {
  try {
    avatars.value = await listAvatars()
  } catch {
    avatars.value = demoAvatars
  }
}

async function handleSave() {
  try {
    const saved = await saveAvatarConfig(currentConfig.value)
    const idx = avatars.value.findIndex((a) => a.id === saved.id)
    if (idx >= 0) {
      avatars.value[idx] = saved
    } else {
      avatars.value.push(saved)
    }
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.success('配置已保存（演示模式）')
  }
}

async function handleActivate(avatar: AvatarConfig) {
  try {
    await activateAvatar(avatar.id)
  } catch {
    // demo mode
  }
  avatars.value.forEach((a) => (a.is_active = a.id === avatar.id))
  ElMessage.success(`已激活"${avatar.name}"`)
}

function editAvatar(avatar: AvatarConfig) {
  currentConfig.value = { ...avatar }
}

onMounted(loadAvatars)
</script>

<template>
  <div class="avatar-view">
    <h1 class="page-title">数字人形象管理</h1>

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
              <div class="avatar-placeholder">{{ avatar.name[0] }}</div>
            </div>
            <div class="avatar-info">
              <h4>{{ avatar.name }}</h4>
              <p>{{ avatar.appearance.style }} | {{ voiceOptions.find(v => v.id === avatar.voice_config.voice_id)?.label || avatar.voice_config.voice_id }}</p>
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

          <el-form-item label="服装风格">
            <el-select v-model="currentConfig.appearance!.style" style="width: 100%">
              <el-option v-for="s in styleOptions" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>

          <el-form-item label="语音音色">
            <el-select v-model="currentConfig.voice_config!.voice_id" style="width: 100%">
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
              v-model="currentConfig.voice_config!.speed"
              :min="0.5"
              :max="2.0"
              :step="0.1"
              show-stops
            />
          </el-form-item>

          <el-form-item label="语调">
            <el-slider
              v-model="currentConfig.voice_config!.pitch"
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
  margin-bottom: 24px;
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

.avatar-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: 700;
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
