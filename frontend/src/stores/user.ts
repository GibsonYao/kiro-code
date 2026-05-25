import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api/auth'
import type { UserInfo, Family, LoginResult } from '@/services/types'

export const useUserStore = defineStore('user', () => {
  // --- State ---
  const token = ref<string>(uni.getStorageSync('token') || '')
  const refreshToken = ref<string>(uni.getStorageSync('refreshToken') || '')
  const userInfo = ref<UserInfo | null>(null)
  const currentFamily = ref<Family | null>(null)
  const families = ref<Family[]>([])

  // --- Getters ---
  const isLoggedIn = computed(() => !!token.value)
  const userId = computed(() => userInfo.value?.id || '')
  const nickname = computed(() => userInfo.value?.nickname || '')
  const avatarUrl = computed(() => userInfo.value?.avatar_url || '')

  // --- Actions ---

  /** 微信授权登录 */
  async function login(code: string): Promise<void> {
    const result: LoginResult = await authApi.wechatLogin(code)
    setTokens(result.access_token, result.refresh_token)
    await fetchUserInfo()
  }

  /** 手机号+验证码登录 */
  async function phoneLogin(phone: string, code: string): Promise<void> {
    const result: LoginResult = await authApi.phoneLogin(phone, code)
    setTokens(result.access_token, result.refresh_token)
    await fetchUserInfo()
  }

  /** 邮箱+密码登录 */
  async function emailLogin(email: string, password: string): Promise<void> {
    const result: LoginResult = await authApi.emailLogin(email, password)
    setTokens(result.access_token, result.refresh_token)
    await fetchUserInfo()
  }

  /** 邮箱注册 */
  async function emailRegister(email: string, password: string, nickname?: string): Promise<void> {
    const result: LoginResult = await authApi.emailRegister(email, password, nickname)
    setTokens(result.access_token, result.refresh_token)
    await fetchUserInfo()
  }

  /** Demo登录（无需凭证） */
  async function demoLogin(): Promise<void> {
    const result: LoginResult = await authApi.demoLogin()
    setTokens(result.access_token, result.refresh_token)
    await fetchUserInfo()
  }

  /** 切换家庭 */
  async function switchFamily(familyId: string): Promise<void> {
    currentFamily.value = families.value.find(f => f.id === familyId) || null
    if (currentFamily.value) {
      uni.setStorageSync('currentFamilyId', familyId)
    }
  }

  /** 退出登录 */
  function logout(): void {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    currentFamily.value = null
    families.value = []
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('currentFamilyId')
    uni.reLaunch({ url: '/pages/login/index' })
  }

  /** 获取用户信息 */
  async function fetchUserInfo(): Promise<void> {
    try {
      const data = await authApi.getMe()
      // /auth/me returns the user object directly
      userInfo.value = data as unknown as UserInfo
      uni.setStorageSync('userInfo', JSON.stringify(userInfo.value))
    } catch {
      // If fetching user info fails, don't logout - token might still be valid
    }
  }

  /** 刷新Token */
  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const result = await authApi.refresh(refreshToken.value)
      setTokens(result.access_token, result.refresh_token)
      return true
    } catch {
      logout()
      return false
    }
  }

  /** 设置Token */
  function setTokens(access: string, refresh: string): void {
    token.value = access
    refreshToken.value = refresh
    uni.setStorageSync('token', access)
    uni.setStorageSync('refreshToken', refresh)
  }

  return {
    // State
    token,
    refreshToken,
    userInfo,
    currentFamily,
    families,
    // Getters
    isLoggedIn,
    userId,
    nickname,
    avatarUrl,
    // Actions
    login,
    phoneLogin,
    emailLogin,
    emailRegister,
    demoLogin,
    switchFamily,
    logout,
    fetchUserInfo,
    refreshAccessToken,
    setTokens,
  }
})
