import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Space, Typography, Divider, message, Alert, Descriptions, Switch, Radio, RadioChangeEvent, Form, Collapse } from 'antd';
import { testApiConnection, setShow401Message } from '../../utils/api';
import api from '../../utils/api';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface ApiResponse {
  status: number;
  data: any;
  error?: string;
}

const ApiTester: React.FC = () => {
  const [token, setToken] = useState<string>(localStorage.getItem('token') || '');
  const [customEndpoint, setCustomEndpoint] = useState<string>('/machines');
  const [responses, setResponses] = useState<Record<string, ApiResponse>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [directRequest, setDirectRequest] = useState<boolean>(false);
  const [apiServer, setApiServer] = useState<string>('http://localhost:8011/api');
  const [authHeader, setAuthHeader] = useState<string>('Bearer');
  const [show401Message, setShow401MessageState] = useState<boolean>(false);
  const [bypassAuth, setBypassAuth] = useState<boolean>(false);
  const [mockUsername, setMockUsername] = useState<string>('admin');
  const [mockPassword, setMockPassword] = useState<string>('password');

  useEffect(() => {
    // 初始加载时获取当前token
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const updateToken = () => {
    localStorage.setItem('token', token);
    message.success('Token已更新，将在下次请求时使用');
  };

  const clearToken = () => {
    localStorage.removeItem('token');
    setToken('');
    message.success('Token已清除');
  };

  const runApiTest = async () => {
    await testApiConnection();
    message.info('查看控制台获取详细测试结果');
  };

  const testEndpoint = async (endpoint: string) => {
    const key = endpoint.replace(/\//g, '_');
    
    setLoading(prev => ({ ...prev, [key]: true }));
    
    try {
      let response;
      
      if (directRequest) {
        // 直接使用axios发送请求，不使用配置的api实例
        const headers: Record<string, string> = {
          'Content-Type': 'application/json'
        };
        
        if (token) {
          headers['Authorization'] = `${authHeader} ${token}`;
        }
        
        // 添加模拟授权参数
        const params: Record<string, string> = {};
        if (bypassAuth) {
          params.mock_username = mockUsername;
          params.mock_password = mockPassword;
          params.bypass_auth = 'true';
        }
        
        response = await axios.get(`${apiServer}${endpoint}`, { 
          headers,
          params
        });
      } else {
        // 使用配置的api实例
        const params = bypassAuth ? {
          mock_username: mockUsername,
          mock_password: mockPassword,
          bypass_auth: 'true'
        } : {};
        
        response = await api.get(endpoint, { params });
      }
      
      setResponses(prev => ({
        ...prev,
        [key]: {
          status: response.status,
          data: response.data
        }
      }));
      
      message.success(`请求成功 (${response.status})`);
    } catch (error: any) {
      console.error('测试端点错误:', error);
      
      setResponses(prev => ({
        ...prev,
        [key]: {
          status: error.response?.status || 0,
          data: error.response?.data || {},
          error: error.message
        }
      }));
      
      message.error(`请求失败: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const renderResponseData = (data: any) => {
    if (!data) return <Text>无数据</Text>;
    
    try {
      return <pre>{JSON.stringify(data, null, 2)}</pre>;
    } catch (e) {
      return <Text>无法显示数据: {String(e)}</Text>;
    }
  };

  const handleApiServerChange = (e: RadioChangeEvent) => {
    setApiServer(e.target.value);
  };

  const toggleShow401Message = (checked: boolean) => {
    setShow401MessageState(checked);
    setShow401Message(checked);
    message.info(`401错误消息提示已${checked ? '开启' : '关闭'}`);
  };

  return (
    <Card title="API连接测试工具">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Title level={4}>Token管理</Title>
        
        <Input.TextArea
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="输入授权Token"
          rows={3}
          style={{ fontFamily: 'monospace' }}
        />
        
        <Space>
          <Button type="primary" onClick={updateToken}>更新Token</Button>
          <Button danger onClick={clearToken}>清除Token</Button>
          <Form.Item label="认证头前缀">
            <Radio.Group value={authHeader} onChange={(e) => setAuthHeader(e.target.value)}>
              <Radio.Button value="Bearer">Bearer</Radio.Button>
              <Radio.Button value="Token">Token</Radio.Button>
              <Radio.Button value="">无前缀</Radio.Button>
            </Radio.Group>
          </Form.Item>
        </Space>
        
        <Divider />
        
        <Title level={4}>请求配置</Title>
        
        <Form layout="vertical">
          <Form.Item label="API服务器">
            <Radio.Group value={apiServer} onChange={handleApiServerChange}>
              <Radio.Button value="http://localhost:8011/api">localhost:8011</Radio.Button>
              <Radio.Button value="http://localhost:8012/api">localhost:8012</Radio.Button>
              <Radio.Button value="http://127.0.0.1:8011/api">127.0.0.1:8011</Radio.Button>
            </Radio.Group>
          </Form.Item>
          
          <Form.Item 
            label="直接请求模式" 
            help="启用后将绕过API拦截器，直接使用axios发送请求"
          >
            <Switch 
              checked={directRequest} 
              onChange={setDirectRequest} 
              checkedChildren="开启" 
              unCheckedChildren="关闭"
            />
          </Form.Item>
          
          <Form.Item 
            label="显示401错误消息" 
            help="开启后将显示拦截器捕获的401错误消息"
          >
            <Switch 
              checked={show401Message} 
              onChange={toggleShow401Message} 
              checkedChildren="显示" 
              unCheckedChildren="不显示"
            />
          </Form.Item>
          
          <Collapse ghost>
            <Panel header="高级选项" key="1">
              <Form.Item 
                label="绕过授权验证" 
                help="添加特殊参数到请求，让后端可以跳过严格的token验证（需要后端支持）"
              >
                <Switch 
                  checked={bypassAuth} 
                  onChange={setBypassAuth} 
                  checkedChildren="开启" 
                  unCheckedChildren="关闭"
                />
              </Form.Item>
              
              {bypassAuth && (
                <>
                  <Form.Item label="模拟用户名">
                    <Input 
                      value={mockUsername} 
                      onChange={(e) => setMockUsername(e.target.value)}
                      placeholder="用于模拟授权的用户名"
                    />
                  </Form.Item>
                  
                  <Form.Item label="模拟密码">
                    <Input.Password 
                      value={mockPassword} 
                      onChange={(e) => setMockPassword(e.target.value)}
                      placeholder="用于模拟授权的密码"
                    />
                  </Form.Item>
                  
                  <Alert 
                    type="info"
                    message="模拟授权说明"
                    description="此功能需要后端支持特殊参数处理。请确保后端已经实现了相应的逻辑，否则此功能无效。"
                    showIcon
                  />
                </>
              )}
            </Panel>
          </Collapse>
        </Form>
        
        <Divider />
        
        <Title level={4}>连接测试</Title>
        
        <Button type="primary" onClick={runApiTest}>
          运行全面测试
        </Button>
        
        <Paragraph>
          全面测试结果将输出到浏览器控制台，按F12查看
        </Paragraph>
        
        <Divider />
        
        <Title level={4}>API端点测试</Title>
        
        <Space style={{ marginBottom: 16 }}>
          <Input 
            value={customEndpoint}
            onChange={(e) => setCustomEndpoint(e.target.value)}
            placeholder="API端点，例如 /machines"
            style={{ width: 300 }}
            addonBefore="GET"
          />
          <Button 
            type="primary" 
            onClick={() => testEndpoint(customEndpoint)}
            loading={loading[customEndpoint.replace(/\//g, '_')]}
          >
            测试
          </Button>
        </Space>
        
        <Paragraph>
          {directRequest ? 
            `将向 ${apiServer}${customEndpoint} 发送请求` : 
            '将使用配置的API实例发送请求'
          }
        </Paragraph>
        
        <Space direction="vertical" style={{ width: '100%' }}>
          {Object.entries(responses).map(([key, response]) => (
            <Card 
              key={key} 
              size="small" 
              title={`${key.replace(/_/g, '/')} 响应`}
              style={{ 
                marginBottom: 16,
                borderColor: response.status >= 200 && response.status < 300 ? '#52c41a' : '#f5222d'
              }}
            >
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="状态码">
                  {response.status}
                </Descriptions.Item>
                
                {response.error && (
                  <Descriptions.Item label="错误">
                    <Alert type="error" message={response.error} />
                  </Descriptions.Item>
                )}
                
                <Descriptions.Item label="响应数据">
                  <div style={{ maxHeight: 300, overflow: 'auto' }}>
                    {renderResponseData(response.data)}
                  </div>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          ))}
        </Space>
      </Space>
    </Card>
  );
};

export default ApiTester; 