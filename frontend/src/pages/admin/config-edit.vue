<template>
  <view class="config-edit-page">
    <view class="page-header">
      <text class="page-title">{{ isEdit ? '编辑配置' : '新增配置' }}</text>
    </view>

    <view class="form-section">
      <!-- 配置Key -->
      <view class="form-item">
        <text class="form-label">配置Key <text class="required">*</text></text>
        <input
          v-model="form.config_key"
          class="form-input"
          placeholder="如: text_generation, image_generation"
        />
      </view>

      <!-- 供应商 -->
      <view class="form-item">
        <text class="form-label">供应商 <text class="required">*</text></text>
        <view class="provider-options">
          <view
            v-for="p in providers"
            :key="p"
            class="provider-option"
            :class="{ active: form.provider === p }"
            @click="form.provider = p"
          >
            {{ p }}
          </view>
        </view>
      </view>

      <!-- 模型名称 -->
      <view class="form-item">
        <text class="form-label">模型名称 <text class="required">*</text></text>
        <input
          v-model="form.model_name"
          class="form-input"
          placeholder="如: qwen-turbo, deepseek-chat"
        />
      </view>

      <!-- API Key -->
      <view class="form-item">
        <text class="form-label">API Key <text class="required">*</text></text>
        <input
          v-model="form.api_key"
          class="form-input"
          :placeholder="isEdit ? '留空则不修改' : '请输入API Key'"
          :password="!showApiKey"
        />
        <view class="input-suffix" @click="showApiKey = !showApiKey">
          <text>{{ showApiKey ? '隐藏' : '显示' }}</text>
        </view>
      </view>

      <!-- API Base URL -->
      <view class="form-item">
        <text class="form-label">API Base URL</text>
        <input
          v-model="form.api_base_url"
          class="form-input"
          placeholder="留空使用默认地址"
        />
      </view>

      <!-- 优先级 -->
      <view class="form-item">
        <text class="form-label">优先级</text>
        <input
          v-model="form.priority"
          class="form-input"
          type="number"
          placeholder="数字越大优先级越高"
        />
      </view>

      <!-- 是否激活 -->
      <view class="form-item row">
        <text class="form-label">激活状态</text>
        <switch :checked="form.is_active" @change="(e: any) => form.is_active = e.detail.value" />
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="form-actions">
      <button class="btn-cancel" @click="handleCancel">取消</button>
      <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '保存中...' : '保存' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { get, post, put } from '@/services/request'

const providers = ['dashscope', 'deepseek', 'openai', 'stable_diffusion']

const isEdit = ref(false)
const configId = ref('')
const showApiKey = ref(false)
const submitting = ref(false)

const form = reactive({
  config_key: '',
  provider: 'dashscope',
  model_name: '',
  api_key: '',
  api_base_url: '',
  priority: '0',
  is_active: true,
})

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as Record<string, any>
  const options = currentPage?.$page?.options || currentPage?.options || {}
  const id = options.id as string | undefined
  if (id) {
    isEdit.value = true
    configId.value = id
    loadConfig(id)
  }
})

async function loadConfig(id: string) {
  try {
    const data = await get<{ items: Array<Record<string, unknown>> }>('/admin/ai-configs')
    const config = data.items.find((c) => c.id === id)
    if (config) {
      form.config_key = config.config_key as string
      form.provider = config.provider as string
      form.model_name = config.model_name as string
      form.api_key = '' // Don't show encrypted key
      form.api_base_url = (config.api_base_url as string) || ''
      form.priority = String(config.priority)
      form.is_active = config.is_active as boolean
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function handleCancel() {
  uni.navigateBack()
}

async function handleSubmit() {
  if (!form.config_key.trim()) {
    uni.showToast({ title: '请输入配置Key', icon: 'none' })
    return
  }
  if (!form.model_name.trim()) {
    uni.showToast({ title: '请输入模型名称', icon: 'none' })
    return
  }
  if (!isEdit.value && !form.api_key.trim()) {
    uni.showToast({ title: '请输入API Key', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      config_key: form.config_key.trim(),
      provider: form.provider,
      model_name: form.model_name.trim(),
      api_base_url: form.api_base_url.trim() || null,
      priority: parseInt(form.priority) || 0,
      is_active: form.is_active,
    }

    if (form.api_key.trim()) {
      payload.api_key = form.api_key.trim()
    }

    if (isEdit.value) {
      await put(`/admin/ai-configs/${configId.value}`, payload)
    } else {
      payload.api_key = form.api_key.trim()
      await post('/admin/ai-configs', payload)
    }

    uni.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.config-edit-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: env(safe-area-inset-bottom);
}

.page-header {
  background: #fff;
  padding: 32rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.page-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.form-section {
  background: #fff;
  margin-top: 16rpx;
  padding: 24rpx 32rpx;
}

.form-item {
  margin-bottom: 28rpx;
  position: relative;

  &.row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}

.form-label {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
  display: block;
  margin-bottom: 12rpx;
}

.required {
  color: #f5222d;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.input-suffix {
  position: absolute;
  right: 24rpx;
  bottom: 20rpx;
  font-size: 24rpx;
  color: #4a90d9;
}

.provider-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.provider-option {
  padding: 12rpx 24rpx;
  background: #f5f6fa;
  border-radius: 8rpx;
  font-size: 26rpx;
  color: #666;
  border: 2rpx solid transparent;

  &.active {
    background: #e6f7ff;
    color: #4a90d9;
    border-color: #4a90d9;
  }
}

.form-actions {
  display: flex;
  gap: 24rpx;
  padding: 32rpx;
}

.btn-cancel {
  flex: 1;
  height: 88rpx;
  background: #f5f6fa;
  color: #666;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-submit {
  flex: 2;
  height: 88rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
