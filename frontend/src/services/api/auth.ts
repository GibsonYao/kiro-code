import { request } from '@/services/request'
import type { LoginResult, MeResponse } from '@/services/types'

export const authApi = {
  /** 微信小程序登录 */
  wechatLogin(code: string): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/wechat-login',
      method: 'POST',
      data: { code },
      skipAuth: true,
    })
  },

  /** 手机号+验证码登录 */
  phoneLogin(phone: string, code: string): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/phone-login',
      method: 'POST',
      data: { phone, code },
      skipAuth: true,
    })
  },

  /** 邮箱+密码登录 */
  emailLogin(email: string, password: string): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/email-login',
      method: 'POST',
      data: { email, password },
      skipAuth: true,
    })
  },

  /** 邮箱注册 */
  emailRegister(email: string, password: string, nickname?: string): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/register',
      method: 'POST',
      data: { email, password, nickname },
      skipAuth: true,
    })
  },

  /** 发送短信验证码 */
  sendCode(phone: string): Promise<{ message: string }> {
    return request<{ message: string }>({
      url: '/auth/send-code',
      method: 'POST',
      data: { phone },
      skipAuth: true,
    })
  },

  /** 刷新Token */
  refresh(refreshToken: string): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/refresh',
      method: 'POST',
      data: { refresh_token: refreshToken },
      skipAuth: true,
    })
  },

  /** Demo登录（无需凭证） */
  demoLogin(): Promise<LoginResult> {
    return request<LoginResult>({
      url: '/auth/demo-login',
      method: 'POST',
      skipAuth: true,
    })
  },

  /** 获取当前用户信息 */
  getMe(): Promise<MeResponse> {
    return request<MeResponse>({
      url: '/auth/me',
      method: 'GET',
    })
  },
}
