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