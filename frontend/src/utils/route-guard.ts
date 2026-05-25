// ============================================
// 路由守卫 - 未登录拦截跳转登录页
// ============================================

/** 不需要登录即可访问的页面白名单 */
const WHITE_LIST = [
  '/pages/login/index',
]

/** 检查是否已登录 */
function isAuthenticated(): boolean {
  return !!uni.getStorageSync('token')
}

/** 初始化路由拦截 */
export function setupRouteGuard(): void {
  // 拦截 uni.navigateTo
  const originalNavigateTo = uni.navigateTo
  uni.navigateTo = ((options: UniApp.NavigateToOptions) => {
    if (shouldIntercept(String(options.url))) {
      uni.reLaunch({ url: '/pages/login/index' })
      return
    }
    originalNavigateTo(options)
  }) as typeof uni.navigateTo

  // 拦截 uni.redirectTo
  const originalRedirectTo = uni.redirectTo
  uni.redirectTo = ((options: UniApp.RedirectToOptions) => {
    if (shouldIntercept(String(options.url))) {
      uni.reLaunch({ url: '/pages/login/index' })
      return
    }
    originalRedirectTo(options)
  }) as typeof uni.redirectTo

  // 拦截 uni.switchTab
  const originalSwitchTab = uni.switchTab
  uni.switchTab = ((options: UniApp.SwitchTabOptions) => {
    if (shouldIntercept(String(options.url))) {
      uni.reLaunch({ url: '/pages/login/index' })
      return
    }
    originalSwitchTab(options)
  }) as typeof uni.switchTab
}

/** 判断是否需要拦截 */
function shouldIntercept(url: string): boolean {
  // 提取路径（去除查询参数）
  const path = url.split('?')[0]

  // 白名单内的页面不拦截
  if (WHITE_LIST.includes(path)) {
    return false
  }

  // 未登录则拦截
  return !isAuthenticated()
}

/** 页面加载时检查登录状态（用于页面onShow中调用） */
export function checkAuth(): boolean {
  if (!isAuthenticated()) {
    uni.reLaunch({ url: '/pages/login/index' })
    return false
  }
  return true
}

export default { setupRouteGuard, checkAuth }
