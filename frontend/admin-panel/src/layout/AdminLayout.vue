<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import {
  HomeFilled,
  Document,
  User,
  DataAnalysis,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const menuItems = [
  { path: '/', label: '数据大屏', icon: HomeFilled },
  { path: '/knowledge', label: '知识库管理', icon: Document },
  { path: '/avatar', label: '数字人管理', icon: User },
  { path: '/analytics', label: '数据分析', icon: DataAnalysis },
]

function navigateTo(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>SmartTour</h2>
        <p>管理后台</p>
      </div>
      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          @click="navigateTo(item.path)"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </nav>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: #1f2937;
  color: white;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sidebar-header p {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.sidebar-nav {
  padding: 12px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: #d1d5db;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: #4f46e5;
  color: white;
}

.nav-item span {
  font-size: 14px;
}

.main-content {
  flex: 1;
  background: #f0f2f5;
  overflow-y: auto;
}
</style>
