import React, { useState, useEffect } from 'react';
import { Button, Space, Card, Spin, Select, Input, message } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import api from '../../utils/api';
import { useStore } from '../../stores';

const { Option } = Select;

interface LogsViewerProps {
  machineId: number;
  projectId?: number; // 可选的项目ID，如果提供则查看特定项目的日志
}

const LogsViewer: React.FC<LogsViewerProps> = ({ machineId, projectId }) => {
  const [logs, setLogs] = useState<string>('');
  const [logType, setLogType] = useState<string>('backend');
  const [loading, setLoading] = useState<boolean>(false);
  const [password, setPassword] = useState<string>('');
  const { token } = useStore();

  const fetchLogs = async () => {
    if (!machineId) return;
    
    try {
      setLoading(true);
      
      // 构建请求URL和参数
      let url = `/machines/${machineId}/logs`;
      let params = { lines: 500 };
      
      // 如果提供了项目ID，则查看特定项目的日志
      if (projectId) {
        url = `/machines/${machineId}/projects/${projectId}/logs`;
      }
      
      // 构建请求体
      const data = { 
        log_type: logType, 
        password: password && password.trim() !== '' ? password : undefined 
      };
      
      const response = await api.post(
        url,
        data,
        { params }
      );
      
      setLogs(response.data.message || '没有日志');
    } catch (error) {
      console.error('获取日志失败:', error);
      message.error('获取日志失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // 设置自动刷新，每10秒
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, [machineId, projectId, logType]);

  return (
    <div style={{ marginTop: 16 }}>
      <Space style={{ marginBottom: 16 }}>
        <Select 
          value={logType} 
          onChange={setLogType}
          style={{ width: 120 }}
        >
          <Option value="backend">后端日志</Option>
          <Option value="frontend">前端日志</Option>
          {projectId && <Option value="deploy">部署日志</Option>}
        </Select>
        <Input.Password 
          placeholder="SSH密码 (可选)" 
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ width: 200 }}
        />
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          onClick={fetchLogs}
          loading={loading}
        >
          刷新日志
        </Button>
      </Space>
      
      <Card>
        <Spin spinning={loading}>
          <div 
            style={{
              backgroundColor: '#f0f0f0',
              padding: 16,
              borderRadius: 4,
              height: 400,
              overflow: 'auto',
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              fontSize: 12
            }}
          >
            {logs || '没有日志数据'}
          </div>
        </Spin>
      </Card>
    </div>
  );
};

export default LogsViewer; 