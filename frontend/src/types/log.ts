/**
 * 日志相关类型定义
 */

// 日志对象类型
export interface Log {
  id: number;
  entity_type: string | null;
  entity_id: number | null;
  category: string;
  operation: string;
  title: string;
  content: string | null;
  status: string | null;
  data: any | null;
  user_id: number | null;
  username: string | null;
  user_ip: string | null;
  created_at: string;
}

// 日志过滤参数
export interface LogFilter {
  entity_type?: string;
  entity_id?: number;
  category?: string;
  operation?: string;
  status?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}

// 日志状态颜色映射
export const LogStatusColors = {
  success: '#52c41a',
  failed: '#ff4d4f',
  warning: '#faad14',
  info: '#1890ff',
};

// 日志分类映射
export const LogCategoryMap = {
  system: '系统',
  operation: '操作',
  security: '安全',
  status: '状态',
  error: '错误',
};

// 常见操作类型映射
export const LogOperationMap: Record<string, string> = {
  create: '创建',
  update: '更新',
  delete: '删除',
  login: '登录',
  logout: '登出',
  deploy: '部署',
  start: '启动',
  stop: '停止',
  check: '检查',
  upload: '上传',
  download: '下载',
}; 