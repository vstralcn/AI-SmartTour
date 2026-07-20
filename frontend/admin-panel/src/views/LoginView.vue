<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Lock, User } from '@element-plus/icons-vue'
import { loginAdmin } from '../services/api'

const route = useRoute()
const router = useRouter()
const username = ref('admin')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  if (!username.value.trim() || !password.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    await loginAdmin(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || '登录失败，请检查服务状态'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-panel" aria-labelledby="login-title">
      <div class="brand">
        <span class="brand-mark">ST</span>
        <div>
          <h1 id="login-title">SmartTour</h1>
          <p>景区运营管理后台</p>
        </div>
      </div>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />

      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="管理员账号">
          <el-input v-model="username" autocomplete="username" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            autocomplete="current-password"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
          :disabled="!username.trim() || !password"
        >
          登录
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #eef1f5;
}

.login-panel {
  width: min(400px, 100%);
  padding: 32px;
  border: 1px solid #d9dee7;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 16px 40px rgba(31, 41, 55, 0.1);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: #334155;
  color: #fff;
  font-weight: 700;
}

.brand h1 {
  color: #1f2937;
  font-size: 22px;
  line-height: 1.2;
}

.brand p {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.el-alert {
  margin-bottom: 18px;
}

.el-button {
  width: 100%;
  margin-top: 6px;
}
</style>
