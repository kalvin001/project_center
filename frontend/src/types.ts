// 为Prism.js添加全局类型定义
declare global {
  interface Window {
    Prism: {
      highlightAll: () => void;
      [key: string]: any;
    };
  }
}

// 确保全局类型定义生效
export {};

// 项目文件
export interface ProjectFile {
  name: string;
  path: string;
  size: number;
  modified: string;
  type: 'file' | 'directory';
  extension?: string;
}

// 项目文件列表响应
export interface ProjectFileList {
  current_path: string;
  directories: ProjectFile[];
  files: ProjectFile[];
  is_empty: boolean;
}

export interface ProjectFormValues {
  name: string
  description?: string
  project_type: string
  repository_url: string
  repository_type: 'git' | 'local'
  tech_stack?: Record<string, any>
  is_active?: boolean
}

// 文件内容响应
export interface FileContent {
  content: string;
  extension: string;
  name: string;
  path: string;
  size: number;
  modified: string;
  is_binary?: boolean;  // 添加是否为二进制文件的标识
}

// 机器定义
export interface Machine {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string;
  description?: string;
  is_online: boolean;
  backend_running: boolean;
  frontend_running: boolean;
  cpu_usage?: string;
  memory_usage?: string;
  disk_usage?: string;
  created_at: string;
  updated_at?: string;
}

// 项目定义
export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  repository_url: string;
  repository_type: string;
  project_type: string;
  tech_stack?: Record<string, any>;
  storage_path: string;
  is_active: boolean;
  last_updated: string;
  created_at: string;
  machines?: Machine[];
}

// 部署定义
export interface Deployment {
  id: number;
  project_id: number;
  machine_id: number;
  environment: string;
  deploy_path: string;
  status: 'pending' | 'success' | 'failed' | 'not_deployed' | 'running' | 'stopped' | 
          'syncing' | 'sync_failed' | 'starting' | 'start_failed' | 'stopping' | 'stop_failed';
  log?: string;
  deployed_at: string;
  project?: Project;
  machine?: Machine;
}

// 部署表单值
export interface DeploymentFormValues {
  project_id: number;
  machine_id: number;
  environment: string;
  deploy_path: string;
} 