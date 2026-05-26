<template>
  <view class="profile-page">
    <!-- 用户信息卡片 -->
    <view class="profile-card">
      <image class="avatar" :src="userStore.avatarUrl || '/static/default-avatar.png'" mode="aspectFill" />
      <view class="user-info">
        <text class="nickname">{{ userStore.nickname || '未设置昵称' }}</text>
        <text class="user-id">ID: {{ userStore.userId ? userStore.userId.slice(0, 8) + '...' : '-' }}</text>
      </view>
    </view>

    <!-- 积分余额卡片 -->
    <view class="points-card" @click="goTo('/pages/points/index')">
      <view class="points-card-inner">
        <view class="points-info">
          <text class="points-label">积分余额</text>
          <text class="points-balance">{{ pointsStore.balance }}</text>
        </view>
        <view class="points-detail">
          <text class="points-sub">累计获得 {{ pointsStore.totalEarned }}</text>
          <text class="points-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 家庭信息 -->
    <view class="section">
      <text class="section-title">我的家庭</text>
      <view v-if="userStore.families.length > 0" class="family-list">
        <view
          v-for="family in userStore.families"
          :key="family.id"
          class="family-item"
          :class="{ active: userStore.currentFamily?.id === family.id }"
          @click="handleSwitchFamily(family.id)"
        >
          <view class="family-info">
            <text class="family-name">{{ family.name }}</text>
            <text class="family-role">{{ family.role === 'admin' ? '管理员' : '成员' }}</text>
          </view>
          <text v-if="userStore.currentFamily?.id === family.id" class="check-icon">✓</text>
        </view>
      </view>
      <view v-else class="empty-family">
        <text class="empty-text">暂未加入家庭</text>
      </view>

      <!-- 家庭操作 -->
      <view class="family-actions">
        <button class="action-btn" @click="showCreateFamily">创建家庭</button>
        <button class="action-btn outline" @click="showJoinFamily">加入家庭</button>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="section">
      <text class="section-title">功能</text>
      <view class="menu-list">
        <view class="menu-item" @click="goTo('/pages/wishes/index')">
          <text class="menu-icon">✨</text>
          <text class="menu-text">我的愿望</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/goals/index')">
          <text class="menu-icon">🎯</text>
          <text class="menu-text">我的目标</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/tasks/index')">
          <text class="menu-icon">📋</text>
          <text class="menu-text">我的任务</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/points/index')">
          <text class="menu-icon">⭐</text>
          <text class="menu-text">积分中心</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/notifications/index')">
          <text class="menu-icon">🔔</text>
          <text class="menu-text">通知中心</text>
          <view class="menu-badge" v-if="notificationStore.unreadCount > 0">
            <text class="menu-badge-text">{{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/reviews/index')">
          <text class="menu-icon">✅</text>
          <text class="menu-text">审核中心</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/family/index')">
          <text class="menu-icon">👨‍👩‍👧‍👦</text>
          <text class="menu-text">家庭成员</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/admin/index')" v-if="userStore.userInfo?.is_admin">
          <text class="menu-icon">🔧</text>
          <text class="menu-text">后台管理</text>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @click="goTo('/pages/settings/index')">
          <text class="menu-icon">⚙️</text>
          <text class="menu-text">设置</text>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 邀请码（当前家庭） -->
    <view class="section" v-if="userStore.currentFamily">
      <text class="section-title">邀请家人</text>
      <view class="invite-card">
        <text class="invite-label">家庭邀请码</text>
        <view class="invite-code-row">
          <text class="invite-code">{{ userStore.currentFamily.invite_code }}</text>
          <button class="copy-btn" @click="copyInviteCode">复制</button>
        </view>
        <text class="invite-hint">分享邀请码给家人，即可加入家庭</text>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="section">
      <view class="menu-item danger" @click="handleLogout">
        <text class="menu-text">退出登录</text>
      </view>
    </view>

    <!-- 创建家庭弹窗 -->
    <view v-if="showCreateModal" class="modal-mask" @click="showCreateModal = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">创建家庭</text>
        <input
          v-model="newFamilyName"
          class="modal-input"
          placeholder="请输入家庭名称"
          maxlength="50"
        />
        <view class="modal-actions">
          <button class="modal-cancel" @click="showCreateModal = false">取消</button>
          <button class="modal-confirm" @click="handleCreateFamily">创建</button>
        </view>
      </view>
    </view>

    <!-- 加入家庭弹窗 -->
    <view v-if="showJoinModal" class="modal-mask" @click="showJoinModal = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">加入家庭</text>
        <input
          v-model="inviteCode"
          class="modal-input"
          placeholder="请输入邀请码"
          maxlength="20"
        />
        <view class="modal-actions">
          <button class="modal-cancel" @click="showJoinModal = false">取消</button>
          <button class="modal-confirm" @click="handleJoinFamily">加入</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { usePointsStore } from '@/stores/points'
import { checkAuth } from '@/utils/route-guard'
import { post } from '@/services/request'

const userStore = useUserStore()
const pointsStore = usePointsStore()

const showCreateModal = ref(false)
const showJoinModal = ref(false)
const newFamilyName = ref('')
const inviteCode = ref('')

onShow(() => {
  checkAuth()
  userStore.fetchUserInfo()
  pointsStore.fetchBalance()
})

function handleSwitchFamily(familyId: string) {
  userStore.switchFamily(familyId)
  uni.showToast({ title: '已切换', icon: 'success' })
}

function showCreateFamily() {
  newFamilyName.value = ''
  showCreateModal.value = true
}

function showJoinFamily() {
  inviteCode.value = ''
  showJoinModal.value = true
}

async function handleCreateFamily() {
  if (!newFamilyName.value.trim()) {
    uni.showToast({ title: '请输入家庭名称', icon: 'none' })
    return
  }
  try {
    await post('/families', { name: newFamilyName.value.trim() })
    showCreateModal.value = false
    uni.showToast({ title: '创建成功', icon: 'success' })
    await userStore.fetchUserInfo()
  } catch {
    uni.showToast({ title: '创建失败', icon: 'none' })
  }
}

async function handleJoinFamily() {
  if (!inviteCode.value.trim()) {
    uni.showToast({ title: '请输入邀请码', icon: 'none' })
    return
  }
  try {
    await post('/families/join', { invite_code: inviteCode.value.trim() })
    showJoinModal.value = false
    uni.showToast({ title: '加入成功', icon: 'success' })
    await userStore.fetchUserInfo()
  } catch {
    uni.showToast({ title: '加入失败，请检查邀请码', icon: 'none' })
  }
}

function copyInviteCode() {
  if (!userStore.currentFamily) return
  uni.setClipboardData({
    data: userStore.currentFamily.invite_code,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    },
  })
}

function goTo(url: string) {
  uni.navigateTo({ url })
}

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
      }
    },
  })
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: env(safe-area-inset-bottom);
}

.profile-card {
  display: flex;
  align-items: center;
  padding: 48rpx 32rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.5);
  margin-right: 24rpx;
  background: rgba(255, 255, 255, 0.2);
}

.user-info {
  flex: 1;
}

.nickname {
  font-size: 36rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  margin-bottom: 8rpx;
}

.user-id {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}

.points-card {
  margin: -20rpx 24rpx 0;
  position: relative;
  z-index: 1;
}

.points-card-inner {
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: 0 8rpx 24rpx rgba(253, 160, 133, 0.3);
}

.points-info {
  display: flex;
  align-items: baseline;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.points-label {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

.points-balance {
  font-size: 56rpx;
  font-weight: 700;
  color: #fff;
}

.points-detail {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.points-sub {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.points-arrow {
  font-size: 36rpx;
  color: rgba(255, 255, 255, 0.8);
}

.section {
  margin-top: 16rpx;
  background: #fff;
  padding: 24rpx 32rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.family-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.family-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: #f9f9fb;
  border-radius: 12rpx;
  border: 2rpx solid transparent;

  &.active {
    border-color: #4a90d9;
    background: #f0f7ff;
  }
}

.family-info {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.family-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.family-role {
  font-size: 22rpx;
  color: #4a90d9;
  background: #e6f7ff;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.check-icon {
  font-size: 32rpx;
  color: #4a90d9;
  font-weight: 600;
}

.empty-family {
  padding: 24rpx 0;
}

.empty-text {
  font-size: 26rpx;
  color: #999;
}

.family-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  height: 72rpx;
  background: #4a90d9;
  color: #fff;
  font-size: 26rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.outline {
    background: transparent;
    color: #4a90d9;
    border: 1rpx solid #4a90d9;
  }
}

.menu-list {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }

  &.danger .menu-text {
    color: #f5222d;
  }
}

.menu-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}

.menu-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.menu-arrow {
  font-size: 32rpx;
  color: #ccc;
}

.invite-card {
  background: #f9f9fb;
  border-radius: 12rpx;
  padding: 24rpx;
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
  height: 56rpx;
  padding: 0 24rpx;
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
  margin-bottom: 32rpx;
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
