import { create } from 'zustand'
import { loginApi } from '../utils/api'
import api from '../utils/api'
import { useNavigate } from 'react-router-dom'

interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
  avatar_url?: string
}

interface AuthState {
  token: string | null
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  updateUser: (userData: User) => void
}

// API基础URL - 使用相对路径，通过Vite代理转发
const API_URL = '/api';

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  loading: false,
  
  login: async (username, password) => {
    set({ loading: true })
    try {
      const response = await loginApi(username, password)
      const { access_token } = response.data
      
      localStorage.setItem('token', access_token)
      set({ token: access_token, loading: false })
      
      // 获取用户信息
      await useAuthStore.getState().checkAuth()
    } catch (error) {
      console.error('登录错误:', error)
      set({ loading: false })
      throw error
    }
  },
  
  register: async (username, email, password) => {
    set({ loading: true })
    try {
      await api.post(`/auth/register`, {
        username,
        email,
        password,
      })
      set({ loading: false })
    } catch (error) {
      console.error('注册错误:', error)
      set({ loading: false })
      throw error
    }
  },
  
  logout: () => {
    localStorage.removeItem('token')
    set({ token: null, user: null })
  },
  
  checkAuth: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ user: null, token: null })
      return
    }
    
    try {
      const response = await api.get(`/auth/me`)
      set({ user: response.data })
    } catch (error) {
      console.error('验证用户错误:', error)
      localStorage.removeItem('token')
      set({ user: null, token: null })
      throw error
    }
  },
  
  updateUser: (userData) => {
    set({ user: userData })
  },
})) 