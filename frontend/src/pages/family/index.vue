<template>
  <view class="family-members-page">
    <!-- 当前家庭信息 -->
    <view class="family-header" v-if="familyStore.currentFamily">
      <view class="family-title">
        <text class="family-name">{{ familyStore.currentFamily.name }}</text>
        <text class="member-count">{{ familyStore.memberCount }}位成员</text>
      </view>
      <view class="header-actions">
        <button class="btn-switch" @click="goTo('/pages/family/switch')">切换</button>
      </view>
    </view>

    <!-- 成员列表 -->
    <view class="members-section">
      <view class="section-header">
        <text class="section-title">家庭成员</text>
        <button class="btn-add" @click="goTo('/pages/family/invite')">+ 添加</button>
      </view>

      <view v-if="familyStore.loading" class="loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="familyStore.members.length === 0" class="empty">
        <text class="empty-text">暂无成员，邀请家人加入吧</text>
      </view>

      <view v-else class="member-list">
        <view
          v-for="member in familyStore.members"
          :key="member.id"
          class="member-card"
        >
          <image
            class="member-avatar"
            :src="member.user_avatar_url || '/static/default-avatar.png'"
            mode="aspectFill"
          />
          <view class="member-info">
            <view class="member-name-row">
              <text class="member-name">{{ member.user_nickname || '未设置' }}</text>
              <text class="member-role" :class="member.role">
                {{ member.role === 'admin' ? '管理员' : '成员' }}
              </text>
            </view>
            <text class="member-appellation" v-if="member.appellation">
              称谓：{{ member.appellation }}
            </text>
            <text class="member-relationship" v-else-if="member.relationship">
              关系：{{ member.relationship }}
            </text>
          </view>
          <view class="member-actions">
            <button class="btn-appellation" @click="openAppellationEdit(member)">
              设置称谓
            </button>
          </view>
        </view>
      </view>
    </view>

    <!-- 邀请码展示 -->
    <view class="invite-section" v-if="familyStore.currentFamily">
      <text class="section-title">邀请家人</text>
      <view class="invite-card">
        <text class="invite-label">家庭邀请码</text>
        <view class="invite-code-row">
          <text class="invite-code">{{ familyStore.inviteCode }}</text>
          <button class="copy-btn" @click="copyInviteCode">复制</button>
        </view>
        <text class="invite-hint">分享邀请码给家人，即可加入家庭</text>
      </view>
    </view>

    <!-- 称谓编辑弹窗 -->
    <view v-if="showAppellationModal" class="modal-mask" @click="showAppellationModal = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">设置称谓</text>
        <text class="modal-subtitle">为 {{ editingMember?.user_nickname }} 设置称谓</text>
        <input
          v-model="appellationInput"
          class="modal-input"
          placeholder="如：爸爸、妈妈、哥哥"
          maxlength="20"
        />
        <view class="modal-actions">
          <button class="modal-cancel" @click="showAppellationModal = false">取消</button>
          <button class="modal-confirm" @click="handleSetAppellation">确定</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useFamilyStore } from '@/stores/family'
import type { FamilyMemberItem } from '@/stores/family'

const familyStore = useFamilyStore()

const showAppellationModal = ref(false)
const editingMember = ref<FamilyMemberItem | null>(null)
const appellationInput = ref('')

onShow(() => {
  familyStore.init()
})

function goTo(url: string) {
  uni.navigateTo({ url })
}

function openAppellationEdit(member: FamilyMemberItem) {
  editingMember.value = member
  appellationInput.value = member.appellation || ''
  showAppellationModal.value = true
}

async function handleSetAppellation() {
  if (!appellationInput.value.trim() || !editingMember.value) {
    uni.showToast({ title: '请输入称谓', icon: 'none' })
    return
  }
  try {
    await familyStore.setAppellation(editingMember.value.id, appellationInput.value.trim())
    showAppellationModal.value = false
    uni.showToast({ title: '设置成功', icon: 'success' })
  } catch {
    uni.showToast({ title: '设置失败', icon: 'none' })
  }
}

function copyInviteCode() {
  uni.setClipboardData({
    data: familyStore.inviteCode,
    success: () => uni.showToast({ title: '已复制', icon: 'success' }),
  })
}
</script>

<style lang="scss" scoped>
.family-members-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding: 24rpx;
  padding-bottom: env(safe-area-inset-bottom);
}

.family-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.family-title {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.family-name {
  font-size: 36rpx;
  font-weight: 700;
  color: #fff;
}

.member-count {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.btn-switch {
  height: 56rpx;
  padding: 0 24rpx;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 24rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.members-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.btn-add {
  height: 52rpx;
  padding: 0 20rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 24rpx;
  border-radius: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading, .empty {
  padding: 48rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.member-card {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
}

.member-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  margin-right: 20rpx;
  background: #e8e8e8;
}

.member-info {
  flex: 1;
}

.member-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 6rpx;
}

.member-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.member-role {
  font-size: 20rpx;
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
  background: #e6f7ff;
  color: #4a90d9;

  &.admin {
    background: #fff7e6;
    color: #fa8c16;
  }
}

.member-appellation, .member-relationship {
  font-size: 24rpx;
  color: #666;
}

.member-actions {
  margin-left: 12rpx;
}

.btn-appellation {
  height: 48rpx;
  padding: 0 16rpx;
  background: transparent;
  color: #4a90d9;
  font-size: 22rpx;
  border: 1rpx solid #4a90d9;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.invite-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.invite-card {
  background: #f9f9fb;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-top: 16rpx;
}

.invite-label {
  font-size: 24rpx;
  color: #999;
  display: block;
  margin-bottom: 12rpx;
}

.invite-code-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.invite-code {
  font-size: 36rpx;
  font-weight: 700;
  color: #4a90d9;
  letter-spacing: 4rpx;
}

.copy-btn {
  height: 52rpx;
  padding: 0 20rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 24rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.invite-hint {
  font-size: 22rpx;
  color: #999;
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-content {
  width: 560rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 48rpx 32rpx;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
  display: block;
  margin-bottom: 12rpx;
}

.modal-subtitle {
  font-size: 26rpx;
  color: #666;
  text-align: center;
  display: block;
  margin-bottom: 24rpx;
}

.modal-input {
  width: 100%;
  height: 80rpx;
  background: #f5f6fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1rpx solid #e8e8e8;
  margin-bottom: 32rpx;
}

.modal-actions {
  display: flex;
  gap: 24rpx;
}

.modal-cancel {
  flex: 1;
  height: 80rpx;
  background: #f5f6fa;
  color: #666;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-confirm {
  flex: 1;
  height: 80rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
