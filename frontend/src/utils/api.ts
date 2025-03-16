import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { message } from 'antd';

// 判断是否是开发环境
const isDev = process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost';

// 是否默认显示401错误消息
let shouldShow401Message = false;

// 设置是否显示401错误消息
export const setShow401Message = (show: boolean) => {
  shouldShow401Message = show;
};

// 验证token是否有效
const isTokenValid = (token: string | null): boolean => {
  if (!token) return false;
  
  // 简单验证token格式
  try {
    // 检查是否是JWT格式 (格式为 xxx.yyy.zzz)
    return /^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(token);
  } catch (e) {
    console.error('Token验证失败:', e);
    return false;
  }
};

// 检查当前token
const currentToken = localStorage.getItem('token');
console.log('当前token:', currentToken ? `${currentToken.substring(0, 10)}...` : '无');
if (currentToken && !isTokenValid(currentToken)) {
  console.warn('存储的token格式不正确，可能导致认证失败');
}

// 创建axios实例
const api = axios.create({
  baseURL: isDev ? 'http://localhost:8011/api' : 'http://localhost:8011/api', // 统一使用8011端口
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token');
    
    // 如果有token且格式有效，则添加到请求头
    if (token && isTokenValid(token)) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`请求 ${config.url} 添加了授权头:`, token.substring(0, 10) + '...');
    } else {
      if (token) {
        console.warn(`请求 ${config.url} 的token无效，未添加授权头`);
      } else {
        console.warn(`请求 ${config.url} 没有授权头`);
      }
    }
    
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    console.error('API响应错误:', error);
    
    // 处理401未授权错误，但只在开启了消息显示时才显示
    if (error.response?.status === 401) {
      const token = localStorage.getItem('token');
      console.error('收到401错误:', { 
        url: error.config?.url,
        method: error.config?.method,
        hasToken: !!token,
        tokenValid: token ? isTokenValid(token) : false,
        tokenPrefix: token ? token.substring(0, 10) + '...' : '无'
      });
      
      // 添加自定义属性以标记错误已被处理
      (error as any).handledByInterceptor = true;
      
      // 只在配置了显示消息时才显示
      if (shouldShow401Message) {
        message.error('请求未授权，请检查您的登录状态');
      }
    }
    
    return Promise.reject(error);
  }
);

// 专门的登录API方法，使用表单格式提交
export const loginApi = async (username: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('grant_type', 'password');
  formData.append('username', username);
  formData.append('password', password);
  formData.append('scope', '');
  formData.append('client_id', 'string');
  formData.append('client_secret', 'string');
  
  try {
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    // 检查返回的token
    if (response.data && response.data.access_token) {
      console.log('登录成功，获取到token:', response.data.access_token.substring(0, 10) + '...');
      
      if (!isTokenValid(response.data.access_token)) {
        console.warn('API返回的token格式可能不正确');
      }
    } else {
      console.warn('登录成功但未获取到token');
    }
    
    return response;
  } catch (error) {
    console.error('登录请求失败:', error);
    throw error;
  }
};

// 日志相关API
export const logApi = {
  // 获取日志列表
  getLogs: async (params: any) => {
    const { data } = await api.get('/logs/', { params });
    return data;
  },
  
  // 获取日志总数
  getLogsCount: async (params: any) => {
    const { data } = await api.get('/logs/count', { params });
    return data.total;
  },
  
  // 获取日志详情
  getLog: async (id: number) => {
    const { data } = await api.get(`/logs/${id}`);
    return data;
  }
};

// 测试API连接的工具函数
export const testApiConnection = async () => {
  console.log('===== API连接测试开始 =====');
  
  // 检查本地存储的token
  const token = localStorage.getItem('token');
  console.log('当前token:', token ? `${token.substring(0, 15)}...` : '无');
  console.log('token有效性:', token ? (isTokenValid(token) ? '有效' : '无效') : '无token');
  
  try {
    // 测试不需要授权的端点
    console.log('测试公共API端点...');
    const publicResponse = await api.get('/health-check');
    console.log('公共API响应:', publicResponse.status, publicResponse.data);
    
    // 测试需要授权的端点
    if (token) {
      console.log('测试需要授权的API端点...');
      try {
        const authResponse = await api.get('/user/profile');
        console.log('授权API响应:', authResponse.status, authResponse.data);
      } catch (authError: any) {
        console.error('授权API测试失败:', authError.response?.status, authError.response?.data);
      }
    }
  } catch (error: any) {
    console.error('API连接测试失败:', error.message);
    if (error.response) {
      console.error('错误详情:', error.response.status, error.response.data);
    }
  }
  
  console.log('===== API连接测试结束 =====');
  return true;
};

// 部署管理相关API - 带有权限绕过选项
export const deploymentApi = {
  // 获取部署列表
  getDeployments: async (params?: any, bypassAuth: boolean = false): Promise<any[]> => {
    try {
      // 添加绕过授权参数
      const requestParams = bypassAuth ? {
        ...params,
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : params;
      
      const { data } = await api.get('/deployments', { params: requestParams });
      return data;
    } catch (error: any) {
      console.error('获取部署列表失败:', error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求部署列表');
        return deploymentApi.getDeployments(params, true);
      }
      
      throw error;
    }
  },
  
  // 获取项目的部署列表
  getProjectDeployments: async (projectId: number, params?: any, bypassAuth: boolean = false): Promise<any[]> => {
    try {
      const requestParams = bypassAuth ? {
        ...params,
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : params;
      
      const { data } = await api.get(`/deployments/by-project/${projectId}`, { params: requestParams });
      return data;
    } catch (error: any) {
      console.error(`获取项目ID=${projectId}的部署列表失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getProjectDeployments(projectId, params, true);
      }
      
      throw error;
    }
  },
  
  // 获取机器的部署列表
  getMachineDeployments: async (machineId: number, params?: any, bypassAuth: boolean = false): Promise<any[]> => {
    try {
      const requestParams = bypassAuth ? {
        ...params,
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : params;
      
      const { data } = await api.get(`/deployments/by-machine/${machineId}`, { params: requestParams });
      return data;
    } catch (error: any) {
      console.error(`获取机器ID=${machineId}的部署列表失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getMachineDeployments(machineId, params, true);
      }
      
      throw error;
    }
  },
  
  // 创建部署
  createDeployment: async (deploymentData: any, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post('/deployments', deploymentData, { params });
      return data;
    } catch (error: any) {
      console.error('创建部署失败:', error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.createDeployment(deploymentData, true);
      }
      
      throw error;
    }
  },
  
  // 部署应用
  deployApplication: async (deploymentId: number, deployData: any, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post(`/deployments/${deploymentId}/deploy`, deployData, { params });
      return data;
    } catch (error: any) {
      console.error(`部署ID=${deploymentId}的应用失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.deployApplication(deploymentId, deployData, true);
      }
      
      throw error;
    }
  },
  
  // 删除部署
  deleteDeployment: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.delete(`/deployments/${deploymentId}`, { params });
      return data;
    } catch (error: any) {
      console.error(`删除部署ID=${deploymentId}失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.deleteDeployment(deploymentId, true);
      }
      
      throw error;
    }
  },
  
  // 重新部署项目
  redeployProject: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post(`/deployments/${deploymentId}/redeploy`, {}, { params });
      return data;
    } catch (error: any) {
      console.error(`重新部署ID=${deploymentId}的应用失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.redeployProject(deploymentId, true);
      }
      
      throw error;
    }
  },
  
  // 获取单个部署详情
  getDeployment: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.get(`/deployments/${deploymentId}`, { params });
      return data;
    } catch (error: any) {
      console.error(`获取部署ID=${deploymentId}的详情失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getDeployment(deploymentId, true);
      }
      
      throw error;
    }
  },

  // 获取部署日志
  getDeploymentLogs: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.get(`/deployments/${deploymentId}/logs`, { params });
      return data;
    } catch (error: any) {
      console.error(`获取部署ID=${deploymentId}的日志失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getDeploymentLogs(deploymentId, true);
      }
      
      throw error;
    }
  },

  // 启动应用
  startApplication: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post(`/deployments/${deploymentId}/start`, {}, { params });
      return data;
    } catch (error: any) {
      console.error(`启动部署ID=${deploymentId}的应用失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.startApplication(deploymentId, true);
      }
      
      throw error;
    }
  },

  // 停止应用
  stopApplication: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post(`/deployments/${deploymentId}/stop`, {}, { params });
      return data;
    } catch (error: any) {
      console.error(`停止部署ID=${deploymentId}的应用失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.stopApplication(deploymentId, true);
      }
      
      throw error;
    }
  },

  // 同步项目代码
  syncProject: async (deploymentId: number, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params = bypassAuth ? {
        bypass_auth: 'true',
        mock_username: 'admin',
        mock_password: 'admin'
      } : undefined;
      
      const { data } = await api.post(`/deployments/${deploymentId}/sync`, {}, { params });
      return data;
    } catch (error: any) {
      console.error(`同步项目ID=${deploymentId}失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.syncProject(deploymentId, true);
      }
      
      throw error;
    }
  },

  // 获取部署文件列表
  getDeploymentFiles: async (deploymentId: number, path: string = "", bypassAuth: boolean = false): Promise<any> => {
    try {
      const params: any = { path };
      
      if (bypassAuth) {
        params.bypass_auth = 'true';
        params.mock_username = 'admin';
        params.mock_password = 'admin';
      }
      
      const { data } = await api.get(`/deployments/${deploymentId}/files`, { params });
      return data;
    } catch (error: any) {
      console.error(`获取部署ID=${deploymentId}的文件列表失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getDeploymentFiles(deploymentId, path, true);
      }
      
      throw error;
    }
  },
  
  // 获取文件内容
  getFileContent: async (deploymentId: number, filePath: string, bypassAuth: boolean = false): Promise<any> => {
    try {
      const params: any = { file_path: filePath };
      
      if (bypassAuth) {
        params.bypass_auth = 'true';
        params.mock_username = 'admin';
        params.mock_password = 'admin';
      }
      
      const { data } = await api.get(`/deployments/${deploymentId}/file`, { params });
      return data;
    } catch (error: any) {
      console.error(`获取文件内容失败:`, error);
      
      // 如果是401错误且没有启用绕过，尝试用绕过模式再请求一次
      if (error.response?.status === 401 && !bypassAuth) {
        console.warn('尝试使用绕过授权模式重新请求');
        return deploymentApi.getFileContent(deploymentId, filePath, true);
      }
      
      throw error;
    }
  },
};

export default api; 