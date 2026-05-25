// ============================================
// API请求封装
// 拦截器、Token自动附加、刷新逻辑、错误处理
// ============================================

const BASE_URL = '/api/v1'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: string | AnyObject | ArrayBuffer
  header?: Record<string, string>
  /** 是否跳过Token附加（用于登录等公开接口） */
  skipAuth?: boolean
}

type AnyObject = Record<string, unknown>

interface RequestResponse<T = unknown> {
  data: T
  statusCode: number
  header: Record<string, string>
}

/** Token刷新锁，防止并发刷新 */
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function onTokenRefreshed(newToken: string): void {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

function addRefreshSubscriber(callback: (token: string) => void): void {
  refreshSubscribers.push(callback)
}

/** 获取存储的Token */
function getToken(): string {
  return uni.getStorageSync('token') || ''
}

function getRefreshToken(): string {
  return uni.getStorageSync('refreshToken') || ''
}

/** 刷新Token */
async function refreshAccessToken(): Promise<string> {
  const rToken = getRefreshToken()
  if (!rToken) {
    throw new Error('No refresh token')
  }

  const res = await uni.request({
    url: `${BASE_URL}/auth/refresh`,
    method: 'POST',
    data: { refresh_token: rToken },
    header: { 'Content-Type': 'application/json' },
  }) as unknown as RequestResponse<{ access_token: string; refresh_token: string }>

  if (res.statusCode === 200 && res.data.access_token) {
    uni.setStorageSync('token', res.data.access_token)
    uni.setStorageSync('refreshToken', res.data.refresh_token)
    return res.data.access_token
  }

  throw new Error('Token refresh failed')
}

/** 处理401错误，尝试刷新Token */
async function handle401<T>(options: RequestOptions): Promise<T> {
  if (isRefreshing) {
    // 等待Token刷新完成后重试
    return new Promise<T>((resolve) => {
      addRefreshSubscriber((newToken: string) => {
        options.header = {
          ...options.header,
          Authorization: `Bearer ${newToken}`,
        }
        resolve(request<T>(options))
      })
    })
  }

  isRefreshing = true
  try {
    const newToken = await refreshAccessToken()
    isRefreshing = false
    onTokenRefreshed(newToken)
    // 用新Token重试原请求
    options.header = {
      ...options.header,
      Authorization: `Bearer ${newToken}`,
    }
    return request<T>(options)
  } catch {
    isRefreshing = false
    refreshSubscribers = []
    // 刷新失败，跳转登录
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.reLaunch({ url: '/pages/login/index' })
    throw new Error('Authentication expired')
  }
}

/** 统一错误处理 */
function handleError(statusCode: number, data: unknown): never {
  const message = (data as { detail?: string })?.detail || '请求失败'

  switch (statusCode) {
    case 400:
      uni.showToast({ title: message, icon: 'none' })
      break
    case 403:
      uni.showToast({ title: '没有权限', icon: 'none' })
      break
    case 404:
      uni.showToast({ title: '资源不存在', icon: 'none' })
      break
    case 422:
      uni.showToast({ title: '参数错误', icon: 'none' })
      break
    case 500:
      uni.showToast({ title: '服务器错误', icon: 'none' })
      break
    default:
      uni.showToast({ title: message, icon: 'none' })
  }

  throw new Error(message)
}

/** 核心请求函数 */
export async function request<T = unknown>(options: RequestOptions): Promise<T> {
  const { url, method = 'GET', data, header = {}, skipAuth = false } = options

  // 自动附加Token
  const requestHeader: Record<string, string> = {
    'Content-Type': 'application/json',
    ...header,
  }

  if (!skipAuth) {
    const token = getToken()
    if (token) {
      requestHeader['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await uni.request({
    url: `${BASE_URL}${url}`,
    method,
    data,
    header: requestHeader,
  }) as unknown as RequestResponse<T>

  // 处理401 - 尝试刷新Token
  if (res.statusCode === 401 && !skipAuth) {
    return handle401<T>(options)
  }

  // 处理其他错误
  if (res.statusCode < 200 || res.statusCode >= 300) {
    handleError(res.statusCode, res.data)
  }

  return res.data
}

/** GET请求 */
export function get<T = unknown>(url: string, params?: Record<string, unknown>): Promise<T> {
  return request<T>({ url, method: 'GET', data: params })
}

/** POST请求 */
export function post<T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> {
  return request<T>({ url, method: 'POST', data })
}

/** PUT请求 */
export function put<T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> {
  return request<T>({ url, method: 'PUT', data })
}

/** DELETE请求 */
export function del<T = unknown>(url: string, data?: Record<string, unknown>): Promise<T> {
  return request<T>({ url, method: 'DELETE', data })
}

export default { request, get, post, put, del }
