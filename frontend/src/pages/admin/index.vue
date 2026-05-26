<template>
  <view class="admin-page">
    <!-- 管理员头部 -->
    <view class="admin-header">
      <text class="admin-title">后台管理</text>
      <text class="admin-desc">AI模型配置管理</text>
    </view>

    <!-- 导航标签 -->
    <view class="nav-tabs">
      <view
        class="nav-tab"
        :class="{ active: activeTab === 'configs' }"
        @click="activeTab = 'configs'"
      >
        AI模型配置
      </view>
      <view
        class="nav-tab"
        :class="{ active: activeTab === 'families' }"
        @click="activeTab = 'families'"
      >
        家庭管理
      </view>
    </view>

    <!-- AI模型配置列表 -->
    <view v-if="activeTab === 'configs'" class="content-area">
      <view class="toolbar">
        <button class="btn-add" @click="goTo('/pages/admin/config-edit')">+ 新增配置</button>
      </view>

      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="configs.length === 0" class="empty">
        <text class="empty-text">暂无AI模型配置</text>
      </view>

      <view v-else class="config-list">
        <view
          v-for="config in configs"
          :key="config.id"
          class="config-card"
        >
          <view class="config-header">
            <view class="config-title-row">
              <text class="config-key">{{ config.config_key }}</text>
              <view class="config-status" :class="{ active: config.is_active }">
                {{ config.is_active ? '已激活' : '已停用' }}
              </view>
            </view>
            <text class="config-priority">优先级: {{ config.priority }}</text>
          </view>

          <view class="config-body">
            <view class="config-field">
              <text class="field-label">供应商</text>
              <text class="field-value">{{ config.provider }}</text>
            </view>
            <view class="config-field">
              <text class="field-label">模型</text>
              <text class="field-value">{{ config.model_name }}</text>
            </view>
            <view class="config-field">
              <text class="field-label">API Key</text>
              <text class="field-value masked">{{ config.api_key }}</text>
            </view>
          </view>

          <view class="config-actions">
            <button class="btn-test" @click="handleTest(config.id)">
              {{ testingId === config.id ? '测试中...' : '测试连接' }}
            </button>
            <button
              class="btn-toggle"
              :class="{ deactivate: config.is_active }"
              @click="handleToggle(config.id)"
            >
              {{ config.is_active ? '停用' : '激活' }}
            </button>
            <button class="btn-edit" @click="goTo(`/pages/admin/config-edit?id=${config.id}`)">
              编辑
            </button>
          </view>

          <!-- 测试结果 -->
          <view v-if="testResults[config.id]" class="test-result" :class="{ success: testResults[config.id].success }">
            <text class="test-message">{{ testResults[config.id].message }}</text>
            <text v-if="testResults[config.id].response_time_ms" class="test-time">
              {{ testResults[config.id].response_time_ms }}ms
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 家庭管理（只读） -->
    <view v-if="activeTab === 'families'" class="content-area">
      <view v-if="familiesLoading" class="loading">
        <text>加载中...</text>
      </view>
      <view v-else-if="familyList.length === 0" class="empty">
        <text class="empty-text">暂无家庭数据</text>
      </view>
      <view v-else class="family-list">
        <view v-for="family in familyList" :key="family.id" class="family-card">
          <view class="family-info">
            <text class="family-name">{{ family.name }}</text>
            <text class="family-meta">{{ family.member_count }}位成员 · 邀请码: {{ family.invite_code }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { get, post, put } from '@/services/request'

interface AIConfig {
  id: string
  config_key: string
  provider: string
  model_name: string
  api_key: string
  api_base_url: string | null
  parameters: Record<string, unknown> | null
  is_active: boolean
  priority: number
  created_at: string
  updated_at: string
}

interface TestResult {
  success: boolean
  message: string
  response_time_ms: number | null
}

interface FamilyItem {
  id: string
  name: string
  invite_code: string
  member_count: number
  created_at: string
}

const activeTab = ref('configs')
const loading = ref(false)
const configs = ref<AIConfig[]>([])
const testingId = ref('')
const testResults = reactive<Record<string, TestResult>>({})

const familiesLoading = ref(false)
const familyList = ref<FamilyItem[]>([])

onShow(() => {
  fetchConfigs()
})

async function fetchConfigs() {
  loading.value = true
  try {
    const data = await get<{ items: AIConfig[] }>('/admin/ai-configs')
    configs.value = data.items
  } catch {
    configs.value = []
  } finally {
    loading.value = false
  }
}

async function fetchFamilies() {
  familiesLoading.value = true
  try {
    const data = await get<{ items: FamilyItem[] }>('/admin/families')
    familyList.value = data.items
  } catch {
    familyList.value = []
  } finally {
    familiesLoading.value = false
  }
}

async function handleTest(configId: string) {
  testingId.value = configId
  try {
    const result = await post<TestResult>(`/admin/ai-configs/${configId}/test`)
    testResults[configId] = result
  } catch {
    testResults[configId] = { success: false, message: '测试请求失败', response_time_ms: null }
  } finally {
    testingId.value = ''
  }
}

async function handleToggle(configId: string) {
  try {
    await put(`/admin/ai-configs/${configId}/activate`)
    await fetchConfigs()
    uni.showToast({ title: '操作成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function goTo(url: string) {
  uni.navigateTo({ url })
}

// Watch tab changes to load data
import { watch } from 'vue'
watch(activeTab, (tab) => {
  if (tab === 'families' && familyList.value.length === 0) {
    fetchFamilies()
  }
})
</script>

<style lang="scss" scoped>
.admin-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: env(safe-area-inset-bottom);
}

.admin-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 48rpx 32rpx 32rpx;
}

.admin-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  margin-bottom: 8rpx;
}

.admin-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}

.nav-tabs {
  display: flex;
  background: #fff;
  padding: 0 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.nav-tab {
  padding: 24rpx 32rpx;
  font-size: 28rpx;
  color: #666;
  position: relative;

  &.active {
    color: #4a90d9;
    font-weight: 600;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 32rpx;
      right: 32rpx;
      height: 4rpx;
      background: #4a90d9;
      border-radius: 2rpx;
    }
  }
}

.content-area {
  padding: 24rpx;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20rpx;
}

.btn-add {
  height: 64rpx;
  padding: 0 24rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 26rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading, .empty {
  padding: 64rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.config-card {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.config-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.config-key {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.config-status {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  background: #fff1f0;
  color: #f5222d;

  &.active {
    background: #f6ffed;
    color: #52c41a;
  }
}

.config-priority {
  font-size: 22rpx;
  color: #999;
}

.config-body {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 16rpx;
}

.config-field {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.field-label {
  font-size: 24rpx;
  color: #999;
  width: 100rpx;
}

.field-value {
  font-size: 24rpx;
  color: #333;

  &.masked {
    font-family: monospace;
    color: #666;
  }
}

.config-actions {
  display: flex;
  gap: 12rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f5f5f5;
}

.btn-test, .btn-toggle, .btn-edit {
  height: 56rpx;
  padding: 0 20rpx;
  font-size: 24rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-test {
  background: #e6f7ff;
  color: #1890ff;
}

.btn-toggle {
  background: #f6ffed;
  color: #52c41a;

  &.deactivate {
    background: #fff1f0;
    color: #f5222d;
  }
}

.btn-edit {
  background: #f5f6fa;
  color: #666;
}

.test-result {
  margin-top: 12rpx;
  padding: 12rpx 16rpx;
  border-radius: 8rpx;
  background: #fff1f0;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &.success {
    background: #f6ffed;
  }
}

.test-message {
  font-size: 24rpx;
  color: #333;
}

.test-time {
  font-size: 22rpx;
  color: #999;
}

.family-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.family-card {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
}

.family-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.family-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.family-meta {
  font-size: 24rpx;
  color: #999;
}
</style>
