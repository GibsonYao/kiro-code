// ============================================
// FamilyStore - 家庭成员管理状态
// ============================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post, put } from '@/services/request'

export interface FamilyInfo {
  id: string
  name: string
  avatar_url: string | null
  invite_code: string
  created_by: string
}

export interface FamilyMemberItem {
  id: string
  family_id: string
  user_id: string
  role: string
  nickname_in_family: string | null
  relationship: string | null
  user_nickname: string | null
  user_avatar_url: string | null
  appellation: string | null
}

export interface UserFamilyItem {
  family_id: string
  family_name: string
  role: string
  is_current: boolean
}

export const useFamilyStore = defineStore('family', () => {
  // --- State ---
  const currentFamily = ref<FamilyInfo | null>(null)
  const members = ref<FamilyMemberItem[]>([])
  const myFamilies = ref<UserFamilyItem[]>([])
  const inviteCode = ref('')
  const loading = ref(false)

  // --- Getters ---
  const memberCount = computed(() => members.value.length)
  const isAdmin = computed(() => {
    const current = myFamilies.value.find(f => f.is_current)
    return current?.role === 'admin'
  })

  // --- Actions ---

  /** 获取当前家庭信息 */
  async function fetchCurrentFamily(): Promise<void> {
    try {
      const data = await get<FamilyInfo>('/families/current')
      currentFamily.value = data
      inviteCode.value = data.invite_code
    } catch {
      // 可能没有当前家庭
      currentFamily.value = null
    }
  }

  /** 获取家庭成员列表 */
  async function fetchMembers(): Promise<void> {
    loading.value = true
    try {
      const data = await get<{ items: FamilyMemberItem[]; total: number }>('/families/members')
      members.value = data.items
    } catch {
      members.value = []
    } finally {
      loading.value = false
    }
  }

  /** 获取用户所有家庭 */
  async function fetchMyFamilies(): Promise<void> {
    try {
      const data = await get<{ items: UserFamilyItem[] }>('/families/my-families')
      myFamilies.value = data.items
    } catch {
      myFamilies.value = []
    }
  }

  /** 创建家庭 */
  async function createFamily(name: string): Promise<FamilyInfo> {
    const data = await post<FamilyInfo>('/families', { name })
    await fetchMyFamilies()
    await fetchCurrentFamily()
    return data
  }

  /** 加入家庭 */
  async function joinFamily(code: string): Promise<void> {
    await post('/families/join', { invite_code: code })
    await fetchMyFamilies()
    await fetchCurrentFamily()
    await fetchMembers()
  }

  /** 切换家庭 */
  async function switchFamily(familyId: string): Promise<void> {
    const data = await put<FamilyInfo>(`/families/switch/${familyId}`)
    currentFamily.value = data
    inviteCode.value = data.invite_code
    uni.setStorageSync('currentFamilyId', familyId)
    await fetchMembers()
    await fetchMyFamilies()
  }

  /** 设置称谓 */
  async function setAppellation(memberId: string, appellation: string): Promise<void> {
    await put(`/families/members/${memberId}/appellation`, { appellation })
    // 更新本地成员列表中的称谓
    const member = members.value.find(m => m.id === memberId)
    if (member) {
      member.appellation = appellation
    }
  }

  /** 初始化加载 */
  async function init(): Promise<void> {
    await Promise.all([
      fetchCurrentFamily(),
      fetchMembers(),
      fetchMyFamilies(),
    ])
  }

  return {
    // State
    currentFamily,
    members,
    myFamilies,
    inviteCode,
    loading,
    // Getters
    memberCount,
    isAdmin,
    // Actions
    fetchCurrentFamily,
    fetchMembers,
    fetchMyFamilies,
    createFamily,
    joinFamily,
    switchFamily,
    setAppellation,
    init,
  }
})
