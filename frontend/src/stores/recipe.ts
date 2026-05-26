import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { recipeApi } from '@/services/api/recipes'
import type { RecipeItem, RecipeCreateRequest } from '@/services/types'

/** 饮食偏好 */
export interface DietPreferences {
  tastes: string[]       // 口味偏好标签
  favorites: string[]    // 喜好食材
  restrictions: string[] // 禁忌食材
}

export const useRecipeStore = defineStore('recipe', () => {
  // --- State ---
  const recipes = ref<RecipeItem[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)
  const loading = ref(false)
  const creating = ref(false)
  const preferences = ref<DietPreferences>({
    tastes: [],
    favorites: [],
    restrictions: [],
  })

  // --- Getters ---
  const isEmpty = computed(() => recipes.value.length === 0 && !loading.value)

  // --- Actions ---

  /** 获取食谱列表 */
  async function fetchRecipes(params: { page?: number; page_size?: number; keyword?: string } = {}): Promise<void> {
    loading.value = true
    try {
      currentPage.value = params.page || 1
      const res = await recipeApi.getRecipes({
        page: currentPage.value,
        page_size: params.page_size || pageSize.value,
      })
      if (currentPage.value === 1) {
        recipes.value = res.items
      } else {
        recipes.value = [...recipes.value, ...res.items]
      }
      total.value = res.total
      hasMore.value = res.has_more
    } catch {
      if (currentPage.value === 1) {
        recipes.value = []
      }
    } finally {
      loading.value = false
    }
  }

  /** 加载更多 */
  async function loadMore(): Promise<void> {
    if (!hasMore.value || loading.value) return
    await fetchRecipes({ page: currentPage.value + 1 })
  }

  /** 创建食谱 */
  async function createRecipe(data: RecipeCreateRequest): Promise<RecipeItem> {
    creating.value = true
    try {
      const recipe = await recipeApi.createRecipe(data)
      recipes.value.unshift(recipe)
      total.value += 1
      return recipe
    } finally {
      creating.value = false
    }
  }

  /** 更新食谱 */
  async function updateRecipe(id: string, data: Partial<RecipeCreateRequest>): Promise<RecipeItem> {
    const recipe = await recipeApi.updateRecipe(id, data)
    const idx = recipes.value.findIndex(r => r.id === id)
    if (idx !== -1) recipes.value[idx] = recipe
    return recipe
  }

  /** 删除食谱 */
  async function deleteRecipe(id: string): Promise<void> {
    await recipeApi.deleteRecipe(id)
    recipes.value = recipes.value.filter(r => r.id !== id)
    total.value -= 1
  }

  /** 更新饮食偏好（本地存储） */
  function updatePreferences(newPrefs: Partial<DietPreferences>): void {
    preferences.value = { ...preferences.value, ...newPrefs }
    // 持久化到本地存储
    uni.setStorageSync('diet_preferences', JSON.stringify(preferences.value))
  }

  /** 加载饮食偏好 */
  function loadPreferences(): void {
    try {
      const stored = uni.getStorageSync('diet_preferences')
      if (stored) {
        preferences.value = JSON.parse(stored)
      }
    } catch {
      // ignore
    }
  }

  /** 重置状态 */
  function reset(): void {
    recipes.value = []
    total.value = 0
    currentPage.value = 1
    hasMore.value = false
    loading.value = false
    creating.value = false
  }

  return {
    // State
    recipes,
    total,
    currentPage,
    pageSize,
    hasMore,
    loading,
    creating,
    preferences,
    // Getters
    isEmpty,
    // Actions
    fetchRecipes,
    loadMore,
    createRecipe,
    updateRecipe,
    deleteRecipe,
    updatePreferences,
    loadPreferences,
    reset,
  }
})
