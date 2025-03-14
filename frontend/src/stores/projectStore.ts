import { create } from 'zustand'
import axios from 'axios'
import { message } from 'antd'
import { ProjectFile, ProjectFileList, FileContent } from '../types'

// API基础URL
const API_URL = 'http://localhost:8011/api';

// 添加项目统计信息接口
interface ProjectStats {
  file_count: number
  total_size_bytes: number
  code_lines: number
  total_size_human: string
  ignore_file_exists: boolean
}

interface Project {
  id: number
  name: string
  description: string
  project_type: string
  repository_url: string
  repository_type: string
  tech_stack: Record<string, any> | null
  storage_path: string
  created_at: string
  last_updated: string
  is_active: boolean
  owner_id: number
}

interface Deployment {
  id: number
  project_id: number
  environment: string
  server_host: string
  server_port: number | null
  deploy_path: string
  status: string
  log: string | null
  deployed_at: string
}

interface ProjectWithDeployments extends Project {
  deployments: Deployment[]
  stats?: ProjectStats // 添加统计信息字段
}

interface ProjectState {
  projects: Project[]
  currentProject: ProjectWithDeployments | null
  loading: boolean
  error: string | null
  
  // 同步进度跟踪
  syncProgress: {
    status: string
    message: string
    progress: number
  }
  
  // 项目基本操作
  fetchProjects: () => Promise<void>
  fetchProject: (id: number) => Promise<void>
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'last_updated' | 'storage_path' | 'owner_id'>) => Promise<number>
  updateProject: (id: number, project: Partial<Project>) => Promise<void>
  deleteProject: (id: number) => Promise<void>
  
  // 项目文件操作
  uploadProject: (id: number, file: File, mode?: string) => Promise<void>
  downloadProject: (id: number) => Promise<void>
  cloneFromGit: (id: number, repositoryUrl: string, branch?: string) => Promise<void>
  
  // 文件浏览操作
  projectFiles: ProjectFileList | null
  currentFileContent: FileContent | null
  fetchProjectFiles: (id: number, path?: string) => Promise<ProjectFileList>
  fetchFileContent: (id: number, filePath: string) => Promise<void>
  
  // 部署操作
  createDeployment: (projectId: number, deployment: Omit<Deployment, 'id' | 'project_id' | 'status' | 'log' | 'deployed_at'>) => Promise<void>
  
  // 项目同步
  syncProject: (id: number) => Promise<void>
  
  // 项目工具
  createIgnoreFile: (projectId: number, content: string) => Promise<void>
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,
  projectFiles: null,
  currentFileContent: null,
  
  // 初始化同步进度状态
  syncProgress: {
    status: '',
    message: '',
    progress: 0
  },
  
  fetchProjects: async () => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_URL}/projects`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      set({ projects: response.data, loading: false })
    } catch (error: any) {
      console.error('获取项目列表错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '获取项目列表失败' 
      })
      throw error
    }
  },
  
  fetchProject: async (id) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      console.log(`正在获取项目${id}的详情...`)
      const response = await axios.get(`${API_URL}/projects/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      console.log(`项目${id}详情API响应:`, response.data)
      
      // 检查必要字段是否存在
      if (!response.data.repository_type) {
        console.warn(`项目${id}缺少repository_type字段，添加默认值'git'`)
        response.data.repository_type = 'git'
      }
      
      set({ currentProject: response.data, loading: false })
    } catch (error: any) {
      console.error('获取项目详情错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '获取项目详情失败' 
      })
      throw error
    }
  },
  
  createProject: async (project) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/projects`, project, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      // 更新项目列表
      const newProjects = [...get().projects, response.data]
      set({ projects: newProjects, loading: false })
      
      message.success('项目创建成功')
      return response.data.id
    } catch (error: any) {
      console.error('创建项目错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '创建项目失败' 
      })
      throw error
    }
  },
  
  updateProject: async (id, project) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const response = await axios.put(`${API_URL}/projects/${id}`, project, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      // 更新项目列表和当前项目
      const updatedProjects = get().projects.map(p => 
        p.id === id ? { ...p, ...response.data } : p
      )
      
      set({ 
        projects: updatedProjects, 
        currentProject: get().currentProject?.id === id 
          ? { ...get().currentProject, ...response.data } as ProjectWithDeployments
          : get().currentProject,
        loading: false 
      })
      
      message.success('项目更新成功')
    } catch (error: any) {
      console.error('更新项目错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '更新项目失败' 
      })
      throw error
    }
  },
  
  deleteProject: async (id) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      await axios.delete(`${API_URL}/projects/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      
      // 更新项目列表
      const filteredProjects = get().projects.filter(p => p.id !== id)
      set({ 
        projects: filteredProjects,
        currentProject: get().currentProject?.id === id ? null : get().currentProject,
        loading: false 
      })
      
      message.success('项目删除成功')
    } catch (error: any) {
      console.error('删除项目错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '删除项目失败' 
      })
      throw error
    }
  },
  
  uploadProject: async (id, file, mode = 'replace') => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)
      formData.append('mode', mode)  // 使用传入的模式
      
      await axios.post(`${API_URL}/projects/upload/${id}`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      })
      
      message.success('项目文件上传成功')
      
      // 刷新项目详情
      await get().fetchProject(id)
    } catch (error: any) {
      console.error('上传项目文件错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '上传项目文件失败' 
      })
      throw error
    }
  },
  
  downloadProject: async (id) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/projects/download/${id}`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        responseType: 'blob',
      })
      
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // 获取文件名
      const contentDisposition = response.headers['content-disposition']
      let filename = 'project.zip'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      set({ loading: false })
    } catch (error: any) {
      console.error('下载项目文件错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '下载项目文件失败' 
      })
      throw error
    }
  },
  
  createDeployment: async (projectId, deployment) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API_URL}/projects/${projectId}/deployments`, {
        ...deployment,
        project_id: projectId,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      message.success('部署任务已创建，请稍后查看部署状态')
      
      // 刷新项目详情
      await get().fetchProject(projectId)
    } catch (error: any) {
      console.error('创建部署任务错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '创建部署任务失败' 
      })
      throw error
    }
  },
  
  // 新增方法：克隆Git仓库
  cloneFromGit: async (id, repositoryUrl, branch) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('repository_url', repositoryUrl)
      if (branch) {
        formData.append('branch', branch)
      }
      
      const response = await axios.post(`${API_URL}/projects/${id}/clone`, formData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      
      message.success('Git仓库克隆成功')
      
      // 刷新项目详情
      await get().fetchProject(id)
      // 刷新文件列表
      await get().fetchProjectFiles(id)
      
      set({ loading: false })
    } catch (error: any) {
      console.error('克隆Git仓库错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '克隆Git仓库失败' 
      })
      throw error
    }
  },
  
  // 新增方法：获取项目文件列表
  fetchProjectFiles: async (id, path = "") => {
    set({ loading: true, error: null })
    console.log(`开始获取项目 ${id} 的文件列表，路径: "${path}"`)
    try {
      const token = localStorage.getItem('token')
      console.log(`使用令牌: ${token?.substring(0, 10)}...`)
      
      const response = await axios.get(`${API_URL}/projects/${id}/files`, {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: { path }
      })
      
      console.log(`获取文件列表成功:`, response.data)
      set({ projectFiles: response.data, loading: false })
      return response.data
    } catch (error: any) {
      console.error('获取项目文件列表错误:', error)
      console.error('错误详情:', error.response?.data)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '获取项目文件列表失败',
        projectFiles: null
      })
      throw error
    }
  },
  
  // 新增方法：获取文件内容
  fetchFileContent: async (id, filePath) => {
    set({ loading: true, error: null })
    console.log(`开始获取项目 ${id} 的文件内容，文件路径: "${filePath}"`)
    try {
      const token = localStorage.getItem('token')
      console.log(`使用令牌: ${token?.substring(0, 10)}...`)
      
      const response = await axios.get(`${API_URL}/projects/${id}/files/content`, {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: { file_path: filePath }
      })
      
      console.log(`获取文件内容成功:`, response.data)
      set({ currentFileContent: response.data, loading: false })
      return response.data
    } catch (error: any) {
      console.error('获取文件内容错误:', error)
      console.error('错误详情:', error.response?.data)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '获取文件内容失败',
        currentFileContent: null
      })
      throw error
    }
  },
  
  // 新增方法：项目同步
  syncProject: async (id) => {
    set({ 
      loading: true, 
      error: null,
      syncProgress: {
        status: '',
        message: '准备同步...',
        progress: 0
      }
    })
    
    try {
      // 创建WebSocket连接
      const ws = new WebSocket(`ws://localhost:8011/api/projects/ws/${id}/sync-progress`);
      
      // 设置WebSocket事件处理程序
      ws.onopen = () => {
        console.log('WebSocket连接已建立，开始同步项目');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('收到同步进度更新:', data);
        
        // 更新同步进度状态
        set({ 
          syncProgress: {
            status: data.status,
            message: data.message,
            progress: data.progress
          }
        });
        
        // 如果同步完成或发生错误，关闭loading状态
        if (data.status === 'complete' || data.status === 'error') {
          set({ loading: false });
          
          // 显示相应消息
          if (data.status === 'complete') {
            message.success('项目同步成功');
          } else if (data.status === 'error') {
            message.error(`项目同步失败: ${data.message}`);
          }
          
          // 关闭WebSocket连接
          ws.close();
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        set({ 
          loading: false,
          error: '同步连接出错',
          syncProgress: {
            status: 'error',
            message: '同步连接出错',
            progress: 0
          }
        });
      };
      
      ws.onclose = () => {
        console.log('WebSocket连接已关闭');
      };
      
      // 发起同步请求
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/projects/${id}/sync`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // 同步成功后自动刷新项目详情
      await get().fetchProject(id);
      
      return response.data;
    } catch (error: any) {
      console.error('项目同步错误:', error);
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '项目同步失败',
        syncProgress: {
          status: 'error',
          message: error.response?.data?.detail || '项目同步失败',
          progress: 0
        }
      });
      throw error;
    }
  },
  
  // 新增方法：创建忽略文件
  createIgnoreFile: async (projectId, content) => {
    set({ loading: true, error: null })
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(`${API_URL}/projects/${projectId}/ignore`, { content }, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      message.success('忽略文件创建成功')
      return response.data
    } catch (error: any) {
      console.error('创建忽略文件错误:', error)
      set({ 
        loading: false, 
        error: error.response?.data?.detail || '创建忽略文件失败' 
      })
      throw error
    }
  },
})) 