<template>
  <view class="create-recipe-page">
    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @click="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="nav-title">{{ isEdit ? '编辑食谱' : 'AI智能添加食谱' }}</text>
      <view class="nav-right">
        <text v-if="isEdit" class="delete-btn" @click="handleDelete">删除</text>
      </view>
    </view>

    <scroll-view class="form-container" scroll-y>
      <!-- AI生成模式（新建时） -->
      <view v-if="!isEdit && !aiGenerated" class="ai-section">
        <view class="ai-intro">
          <text class="ai-emoji">🤖</text>
          <text class="ai-title">AI智能生成食谱</text>
          <text class="ai-desc">输入菜品名称，AI自动生成食材清单和做法步骤</text>
        </view>

        <view class="form-group">
          <text class="form-label">菜品名称 *</text>
          <input
            v-model="form.name"
            class="form-input"
            placeholder="如：红烧肉、番茄炒蛋、宫保鸡丁"
            maxlength="256"
          />
        </view>

        <view class="form-group">
          <text class="form-label">描述（可选）</text>
          <textarea
            v-model="form.description"
            class="form-textarea"
            placeholder="简单描述口味或特殊要求"
            :maxlength="200"
          />
        </view>

        <view class="ai-generate-bar">
          <button
            class="ai-generate-btn"
            :disabled="!form.name.trim() || aiGenerating"
            @click="handleAiGenerate"
          >
            <text v-if="aiGenerating">✨ AI生成中...</text>
            <text v-else>✨ AI一键生成食谱</text>
          </button>
          <text class="manual-link" @click="switchToManual">手动填写 ›</text>
        </view>

        <!-- AI生成中动画 -->
        <view v-if="aiGenerating" class="ai-loading">
          <view class="loading-dots">
            <view class="dot"></view>
            <view class="dot"></view>
            <view class="dot"></view>
          </view>
          <text class="loading-text">AI正在为您生成食谱...</text>
          <text class="loading-hint">正在分析食材搭配和烹饪步骤</text>
        </view>
      </view>

      <!-- 手动编辑模式 / AI生成结果 -->
      <view v-if="isEdit || aiGenerated || manualMode">
        <!-- 食谱名称 -->
        <view class="form-group">
          <text class="form-label">食谱名称 *</text>
          <input
            v-model="form.name"
            class="form-input"
            placeholder="请输入食谱名称"
            maxlength="256"
          />
        </view>

        <!-- AI生成标记 -->
        <view v-if="aiGenerated" class="ai-badge">
          <text class="badge-text">✨ AI已生成 - 可自由编辑调整</text>
        </view>

        <!-- 描述 -->
        <view class="form-group">
          <text class="form-label">描述</text>
          <textarea
            v-model="form.description"
            class="form-textarea"
            placeholder="简单描述这道菜（可选）"
            :maxlength="500"
          />
        </view>

        <!-- 食材列表 -->
        <view class="form-group">
          <view class="label-row">
            <text class="form-label">食材</text>
            <text class="add-item-btn" @click="addIngredient">+ 添加</text>
          </view>
          <view class="item-list">
            <view
              v-for="(item, idx) in form.ingredients"
              :key="idx"
              class="item-row"
            >
              <input
                v-model="form.ingredients[idx]"
                class="item-input"
                :placeholder="'食材 ' + (idx + 1)"
              />
              <text class="remove-item" @click="removeIngredient(idx)">✕</text>
            </view>
          </view>
        </view>

        <!-- 步骤列表 -->
        <view class="form-group">
          <view class="label-row">
            <text class="form-label">做法步骤</text>
            <text class="add-item-btn" @click="addStep">+ 添加</text>
          </view>
          <view class="item-list">
            <view
              v-for="(item, idx) in form.steps"
              :key="idx"
              class="item-row step-row"
            >
              <text class="step-number">{{ idx + 1 }}</text>
              <input
                v-model="form.steps[idx]"
                class="item-input"
                :placeholder="'步骤 ' + (idx + 1)"
              />
              <text class="remove-item" @click="removeStep(idx)">✕</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 提交按钮 -->
    <view v-if="isEdit || aiGenerated || manualMode" class="submit-bar">
      <button
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="handleSubmit"
      >
        {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '添加食谱') }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { recipeApi } from '@/services/api/recipes'

const isEdit = ref(false)
const editId = ref('')
const submitting = ref(false)
const aiGenerating = ref(false)
const aiGenerated = ref(false)
const manualMode = ref(false)

const form = ref({
  name: '',
  description: '',
  ingredients: [''] as string[],
  steps: [''] as string[],
})

const canSubmit = computed(() => form.value.name.trim().length > 0)

onLoad((query) => {
  if (query?.id) {
    isEdit.value = true
    editId.value = query.id
    loadRecipe(query.id)
  }
})

async function loadRecipe(id: string) {
  try {
    const recipe = await recipeApi.getRecipe(id)
    form.value.name = recipe.name
    form.value.description = recipe.description || ''
    form.value.ingredients = recipe.ingredients && recipe.ingredients.length > 0 ? [...recipe.ingredients] : ['']
    form.value.steps = recipe.steps && recipe.steps.length > 0 ? [...recipe.steps] : ['']
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

function goBack() {
  uni.navigateBack()
}

function switchToManual() {
  manualMode.value = true
}

async function handleAiGenerate() {
  if (!form.value.name.trim() || aiGenerating.value) return

  aiGenerating.value = true
  try {
    // Simulate AI generation (in production this would call an AI endpoint)
    await new Promise(resolve => setTimeout(resolve, 2000))

    // Generate mock AI content based on dish name
    const dishName = form.value.name.trim()
    form.value.ingredients = generateMockIngredients(dishName)
    form.value.steps = generateMockSteps(dishName)
    if (!form.value.description) {
      form.value.description = `家常${dishName}，简单易做，营养美味`
    }
    aiGenerated.value = true
    uni.showToast({ title: 'AI生成完成', icon: 'success' })
  } catch {
    uni.showToast({ title: 'AI生成失败，请手动填写', icon: 'none' })
    manualMode.value = true
  } finally {
    aiGenerating.value = false
  }
}

function generateMockIngredients(name: string): string[] {
  const commonIngredients: Record<string, string[]> = {
    default: ['主料 适量', '葱 少许', '姜 少许', '蒜 少许', '盐 适量', '生抽 1勺', '食用油 适量'],
  }
  if (name.includes('红烧肉')) {
    return ['五花肉 500g', '冰糖 30g', '生抽 2勺', '老抽 1勺', '料酒 2勺', '八角 2个', '桂皮 1小块', '葱段 适量', '姜片 3片']
  }
  if (name.includes('番茄') || name.includes('西红柿')) {
    return ['番茄 2个', '鸡蛋 3个', '葱花 少许', '盐 适量', '糖 1小勺', '食用油 适量']
  }
  if (name.includes('鸡')) {
    return ['鸡肉 300g', '花生米 50g', '干辣椒 6个', '花椒 1小勺', '葱段 适量', '姜片 3片', '蒜末 适量', '生抽 2勺', '醋 1勺', '糖 1勺', '淀粉 适量']
  }
  return commonIngredients.default
}

function generateMockSteps(name: string): string[] {
  if (name.includes('红烧肉')) {
    return ['五花肉切块，冷水下锅焯水去血沫，捞出备用', '锅中放少许油，加入冰糖小火炒至焦糖色', '放入五花肉翻炒上色', '加入葱姜、八角、桂皮，倒入料酒、生抽、老抽', '加入热水没过肉块，大火烧开后转小火炖40分钟', '大火收汁至浓稠即可出锅']
  }
  if (name.includes('番茄') || name.includes('西红柿')) {
    return ['番茄洗净切块，鸡蛋打散备用', '锅中放油烧热，倒入蛋液炒至凝固盛出', '锅中再放少许油，放入番茄翻炒出汁', '加入少许糖和盐调味', '倒入炒好的鸡蛋翻炒均匀', '撒上葱花出锅']
  }
  return ['准备食材，洗净切好备用', '锅中放油烧热，爆香葱姜蒜', '放入主料翻炒至变色', '加入调味料翻炒均匀', '大火收汁，出锅装盘']
}

function addIngredient() {
  form.value.ingredients.push('')
}

function removeIngredient(idx: number) {
  if (form.value.ingredients.length > 1) {
    form.value.ingredients.splice(idx, 1)
  }
}

function addStep() {
  form.value.steps.push('')
}

function removeStep(idx: number) {
  if (form.value.steps.length > 1) {
    form.value.steps.splice(idx, 1)
  }
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    const ingredients = form.value.ingredients.filter(i => i.trim())
    const steps = form.value.steps.filter(s => s.trim())

    const data = {
      name: form.value.name.trim(),
      description: form.value.description.trim() || undefined,
      ingredients: ingredients.length > 0 ? ingredients : undefined,
      steps: steps.length > 0 ? steps : undefined,
    }

    if (isEdit.value) {
      await recipeApi.updateRecipe(editId.value, data)
      uni.showToast({ title: '保存成功', icon: 'success' })
    } else {
      await recipeApi.createRecipe(data)
      uni.showToast({ title: '添加成功', icon: 'success' })
    }
    setTimeout(() => uni.navigateBack(), 1000)
  } catch {
    uni.showToast({ title: isEdit.value ? '保存失败' : '添加失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定要删除这个食谱吗？',
    confirmColor: '#f5222d',
    success: async (res) => {
      if (res.confirm) {
        try {
          await recipeApi.deleteRecipe(editId.value)
          uni.showToast({ title: '已删除', icon: 'success' })
          setTimeout(() => uni.navigateBack(), 800)
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.create-recipe-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f6fa;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 88rpx 32rpx 24rpx;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.nav-back {
  width: 64rpx;
}

.back-icon {
  font-size: 36rpx;
  color: #fff;
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #fff;
}

.nav-right {
  width: 64rpx;
  display: flex;
  justify-content: flex-end;
}

.delete-btn {
  font-size: 28rpx;
  color: #fff;
}

.form-container {
  flex: 1;
  padding: 24rpx 32rpx;
}

.ai-section {
  margin-bottom: 24rpx;
}

.ai-intro {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 32rpx;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
}

.ai-emoji {
  font-size: 72rpx;
  margin-bottom: 16rpx;
}

.ai-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.ai-desc {
  font-size: 26rpx;
  color: #999;
  text-align: center;
}

.ai-generate-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  margin-top: 24rpx;
}

.ai-generate-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.5;
  }
}

.manual-link {
  font-size: 26rpx;
  color: #4a90d9;
}

.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48rpx 0;
}

.loading-dots {
  display: flex;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;

  &:nth-child(1) { animation-delay: -0.32s; }
  &:nth-child(2) { animation-delay: -0.16s; }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.loading-hint {
  font-size: 24rpx;
  color: #999;
}

.ai-badge {
  background: #f0f5ff;
  border-radius: 8rpx;
  padding: 12rpx 20rpx;
  margin-bottom: 24rpx;
}

.badge-text {
  font-size: 24rpx;
  color: #667eea;
}

.form-group {
  margin-bottom: 32rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 12rpx;
}

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.add-item-btn {
  font-size: 26rpx;
  color: #4a90d9;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.item-row {
  display: flex;
  align-items: center;
  gap: 12rpx;

  &.step-row {
    align-items: center;
  }
}

.step-number {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-input {
  flex: 1;
  height: 72rpx;
  background: #fff;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 26rpx;
  border: 1rpx solid #e8e8e8;
}

.remove-item {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  color: #f5222d;
  flex-shrink: 0;
}

.submit-bar {
  padding: 24rpx 32rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.submit-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &[disabled] {
    opacity: 0.5;
  }
}
</style>
