<template>
  <view class="login-page">
    <view class="login-header">
      <image class="logo" src="/static/logo.png" mode="aspectFit" />
      <text class="app-name">小灶AI家庭管家</text>
      <text class="app-desc">让家庭生活更有条理</text>
    </view>

    <view class="login-body">
      <!-- 微信授权登录（小程序端） -->
      <!-- #ifdef MP-WEIXIN -->
      <view v-if="loginMode === 'wechat'" class="login-section">
        <button
          class="btn-wechat"
          :loading="loading"
          @tap="handleWechatLogin"
        >
          <text class="btn-icon">&#xe600;</text>
          <text>微信授权登录</text>
        </button>
        <view class="switch-mode" @tap="loginMode = 'email'">
          <text>使用邮箱登录</text>
        </view>
      </view>
      <!-- #endif -->

      <!-- 邮箱密码登录 -->
      <view v-if="loginMode === 'email'" class="login-section">
        <!-- 快速体验按钮 -->
        <button
          class="btn-demo"
          :loading="loading"
          @tap="handleDemoLogin"
        >
          🚀 快速体验（无需注册）
        </button>

        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">或</text>
          <view class="divider-line"></view>
        </view>

        <view class="input-group">
          <view class="input-item">
            <text class="input-label">邮箱</text>
            <input
              v-model="email"
              type="text"
              placeholder="请输入邮箱地址"
              class="input-field"
            />
          </view>
          <view class="input-item">
            <text class="input-label">密码</text>
            <input
              v-model="password"
              type="password"
              placeholder="请输入密码（至少6位）"
              class="input-field"
            />
          </view>
        </view>

        <button
          class="btn-login"
          :loading="loading"
          :disabled="!canEmailLogin"
          @tap="handleEmailLogin"
        >
          登录
        </button>

        <button
          class="btn-register"
          :loading="loading"
          :disabled="!canEmailLogin"
          @tap="handleEmailRegister"
        >
          注册新账号
        </button>

        <view class="switch-mode" @tap="loginMode = 'phone'">
          <text>使用手机号登录</text>
        </view>
      </view>

      <!-- 手机号验证码登录 -->
      <view v-if="loginMode === 'phone'" class="login-section">
        <view class="input-group">
          <view class="input-item">
            <text class="input-label">手机号</text>
            <input
              v-model="phone"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
              class="input-field"
            />
          </view>
          <view class="input-item">
            <text class="input-label">验证码</text>
            <view class="code-row">
              <input
                v-model="code"
                type="number"
                maxlength="6"
                placeholder="请输入验证码"
                class="input-field code-input"
              />
              <button
                class="btn-code"
                :disabled="codeCooldown > 0"
                @tap="handleSendCode"
              >
                {{ codeCooldown > 0 ? `${codeCooldown}s` : '获取验证码' }}
              </button>
            </view>
          </view>
        </view>

        <button
          class="btn-login"
          :loading="loading"
          :disabled="!canPhoneLogin"
          @tap="handlePhoneLogin"
        >
          登录
        </button>

        <view class="switch-mode" @tap="loginMode = 'email'">
          <text>使用邮箱登录</text>
        </view>
      </view>
    </view>

    <view class="login-footer">
      <text class="agreement">
        登录即表示同意
        <text class="link">《用户协议》</text>
        和
        <text class="link">《隐私政策》</text>
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/services/api/auth'

// 默认登录方式：小程序端默认微信登录，H5端默认邮箱登录
let defaultMode: 'wechat' | 'phone' | 'email' = 'email'
// #ifdef MP-WEIXIN
defaultMode = 'wechat'
// #endif
const loginMode = ref<'wechat' | 'phone' | 'email'>(defaultMode)

const phone = ref('')
const code = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const codeCooldown = ref(0)

const userStore = useUserStore()

const canPhoneLogin = computed(() => {
  return phone.value.length === 11 && code.value.length >= 4
})

const canEmailLogin = computed(() => {
  return email.value.includes('@') && password.value.length >= 6
})

/** 微信授权登录 */
async function handleWechatLogin() {
  loading.value = true
  try {
    // #ifdef MP-WEIXIN
    const loginResult = await uni.login({ provider: 'weixin' })
    await userStore.login(loginResult.code)
    uni.switchTab({ url: '/pages/home/index' })
    // #endif
  } catch (err) {
    uni.showToast({ title: '登录失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 邮箱登录 */
async function handleEmailLogin() {
  if (!canEmailLogin.value) return
  loading.value = true
  try {
    await userStore.emailLogin(email.value, password.value)
    uni.switchTab({ url: '/pages/home/index' })
  } catch {
    uni.showToast({ title: '邮箱或密码错误', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** Demo快速体验 */
async function handleDemoLogin() {
  loading.value = true
  try {
    await userStore.demoLogin()
    uni.switchTab({ url: '/pages/home/index' })
  } catch {
    uni.showToast({ title: '登录失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 邮箱注册 */
async function handleEmailRegister() {
  if (!canEmailLogin.value) return
  loading.value = true
  try {
    await userStore.emailRegister(email.value, password.value)
    uni.switchTab({ url: '/pages/home/index' })
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '注册失败，该邮箱可能已注册'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 发送验证码 */
async function handleSendCode() {
  if (phone.value.length !== 11) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }

  try {
    await authApi.sendCode(phone.value)
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    startCooldown()
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  }
}

/** 手机号登录 */
async function handlePhoneLogin() {
  if (!canPhoneLogin.value) return
  loading.value = true
  try {
    await userStore.phoneLogin(phone.value, code.value)
    uni.switchTab({ url: '/pages/home/index' })
  } catch {
    uni.showToast({ title: '登录失败，请检查验证码', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 验证码倒计时 */
function startCooldown() {
  codeCooldown.value = 60
  const timer = setInterval(() => {
    codeCooldown.value--
    if (codeCooldown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: $spacing-xl;
  background-color: $color-background;
}

.login-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 120rpx;
  margin-bottom: 80rpx;

  .logo {
    width: 160rpx;
    height: 160rpx;
    margin-bottom: $spacing-lg;
  }

  .app-name {
    font-size: $font-size-xxl;
    font-weight: $font-weight-bold;
    color: $color-text-primary;
    margin-bottom: $spacing-xs;
  }

  .app-desc {
    font-size: $font-size-md;
    color: $color-text-secondary;
  }
}

.login-body {
  flex: 1;
}

.login-section {
  .input-group {
    margin-bottom: $spacing-xl;
  }

  .input-item {
    margin-bottom: $spacing-lg;

    .input-label {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin-bottom: $spacing-xs;
      display: block;
    }

    .input-field {
      width: 100%;
      height: 96rpx;
      background-color: $color-background-card;
      border: 2rpx solid $color-border;
      border-radius: $radius-md;
      padding: 0 $spacing-lg;
      font-size: $font-size-base;
    }
  }

  .code-row {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .code-input {
      flex: 1;
    }

    .btn-code {
      flex-shrink: 0;
      height: 96rpx;
      line-height: 96rpx;
      padding: 0 $spacing-lg;
      font-size: $font-size-sm;
      color: $color-primary;
      background-color: transparent;
      border: 2rpx solid $color-primary;
      border-radius: $radius-md;

      &[disabled] {
        color: $color-text-disabled;
        border-color: $color-border;
      }
    }
  }
}

.btn-wechat {
  width: 100%;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;
  background-color: #07C160;
  color: #ffffff;
  font-size: $font-size-lg;
  font-weight: $font-weight-medium;
  border-radius: $radius-lg;
  border: none;

  .btn-icon {
    font-size: 40rpx;
  }
}

.btn-login {
  width: 100%;
  height: 96rpx;
  background-color: $color-primary;
  color: #ffffff;
  font-size: $font-size-lg;
  font-weight: $font-weight-medium;
  border-radius: $radius-lg;
  border: none;

  &[disabled] {
    background-color: $color-text-disabled;
  }
}

.btn-register {
  width: 100%;
  height: 96rpx;
  background-color: transparent;
  color: $color-primary;
  font-size: $font-size-lg;
  font-weight: $font-weight-medium;
  border-radius: $radius-lg;
  border: 2rpx solid $color-primary;
  margin-top: $spacing-md;
}

.btn-demo {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  font-size: $font-size-lg;
  font-weight: $font-weight-medium;
  border-radius: $radius-lg;
  border: none;
}

.divider {
  display: flex;
  align-items: center;
  margin: $spacing-xl 0;

  .divider-line {
    flex: 1;
    height: 1rpx;
    background-color: $color-border;
  }

  .divider-text {
    padding: 0 $spacing-lg;
    font-size: $font-size-sm;
    color: $color-text-placeholder;
  }
}

.switch-mode {
  text-align: center;
  margin-top: $spacing-xl;

  text {
    font-size: $font-size-md;
    color: $color-primary;
  }
}

.login-footer {
  padding-bottom: 60rpx;
  text-align: center;

  .agreement {
    font-size: $font-size-xs;
    color: $color-text-placeholder;

    .link {
      color: $color-primary;
    }
  }
}
</style>
