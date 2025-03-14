import { create } from 'zustand'
import axios from 'axios'

interface User {
  id: number
  username: string
  email: string
  is_admin: boolean
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

// API基础URL
const API_URL = 'http://localhost:8011/api';

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('token'),
  user: null,
  loading: false,
  
  login: async (username, password) => {
    set({ loading: true })
    try {
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      
      const response = await axios.post(`${API_URL}/auth/login`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      })
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
      await axios.post(`${API_URL}/auth/register`, {
        username,
        email,
        password,
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
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
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
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