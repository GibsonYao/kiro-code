// ============================================
// 食谱模块 API
// ============================================

import { get, post, put, del } from '../request'
import type {
  RecipeItem,
  RecipeListResponse,
  RecipeCreateRequest,
  RecipeUpdateRequest,
  FoodPreferenceSummaryResponse,
  FoodPreferenceItem,
  FoodPreferenceUpdateRequest,
  RecipeGenerateResponse,
} from '../types'

export const recipeApi = {
  /** 获取食谱列表（分页） */
  getRecipes(params: { page?: number; page_size?: number } = {}): Promise<RecipeListResponse> {
    return get<RecipeListResponse>('/recipes', params)
  },

  /** 获取单个食谱 */
  getRecipe(id: string): Promise<RecipeItem> {
    return get<RecipeItem>(`/recipes/${id}`)
  },

  /** 创建食谱 */
  createRecipe(data: RecipeCreateRequest): Promise<RecipeItem> {
    return post<RecipeItem>('/recipes', data as unknown as Record<string, unknown>)
  },

  /** 更新食谱 */
  updateRecipe(id: string, data: RecipeUpdateRequest): Promise<RecipeItem> {
    return put<RecipeItem>(`/recipes/${id}`, data as unknown as Record<string, unknown>)
  },

  /** 删除食谱 */
  deleteRecipe(id: string): Promise<void> {
    return del<void>(`/recipes/${id}`)
  },

  /** AI生成食谱内容（食材清单和做法步骤） */
  generateRecipeContent(recipeId: string, dishName?: string): Promise<RecipeGenerateResponse> {
    const data = dishName ? { dish_name: dishName } : {}
    return post<RecipeGenerateResponse>(`/recipes/${recipeId}/generate`, data)
  },

  /** AI生成食谱预览（创建前预览，不保存） */
  generateRecipePreview(dishName: string): Promise<RecipeGenerateResponse> {
    return post<RecipeGenerateResponse>('/recipes/generate-preview', { dish_name: dishName })
  },

  /** 获取家庭成员饮食偏好汇总 */
  getPreferencesSummary(): Promise<FoodPreferenceSummaryResponse> {
    return get<FoodPreferenceSummaryResponse>('/recipes/preferences')
  },

  /** 更新家庭成员饮食偏好 */
  updatePreferences(userId: string, data: FoodPreferenceUpdateRequest): Promise<FoodPreferenceItem> {
    return put<FoodPreferenceItem>(`/recipes/preferences/${userId}`, data as unknown as Record<string, unknown>)
  },
}
