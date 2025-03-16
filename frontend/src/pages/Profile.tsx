import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Form, 
  Input, 
  Button, 
  Divider, 
  message, 
  Avatar, 
  Row, 
  Col,
  Upload,
  Skeleton,
  Space,
  Modal
} from 'antd';
import { UserOutlined, MailOutlined, LockOutlined, UploadOutlined, CameraOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import axios from 'axios';
import { API_URL, STATIC_URL } from '../utils/constants';

const { Title, Text } = Typography;

interface UserProfile {
  id: number;
  username: string;
  email: string;
  created_at: string;
  updated_at: string | null;
  is_active: boolean;
  is_admin: boolean;
  avatar_url?: string;
}

// 定义一个通用的用户数据类型
type UserData = Partial<UserProfile>;

const Profile: React.FC = () => {
  const { user, token, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [passwordForm] = Form.useForm();
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState('');

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  // 格式化日期，避免无效日期报错
  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '未知';
    try {
      return new Date(dateStr).toLocaleString();
    } catch (error) {
      return '日期无效';
    }
  };

  const fetchUserProfile = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
      if (response.data.avatar_url) {
        setAvatarUrl(response.data.avatar_url);
        // 调试输出头像URL
        console.log('Avatar URL:', response.data.avatar_url);
        console.log('Full Avatar URL:', `${STATIC_URL}${response.data.avatar_url}`);
      } else {
        console.log('没有头像URL');
      }
      // 打印整个用户数据对象
      console.log('User data:', response.data);
    } catch (error) {
      message.error('获取个人资料失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (values: any) => {
    setLoading(true);
    try {
      const response = await axios.put(`${API_URL}/auth/update`, values, {
        headers: { Authorization: `Bearer ${token}` }
      });
      updateUser(response.data);
      message.success('个人资料更新成功');
    } catch (error) {
      message.error('更新失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (values: any) => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/auth/change-password`, values, {
        headers: { Authorization: `Bearer ${token}` }
      });
      message.success('密码更新成功');
      passwordForm.resetFields();
    } catch (error) {
      message.error('密码更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (options: any) => {
    const { file, onSuccess, onError } = options;
    const formData = new FormData();
    formData.append('avatar', file);
    setUploading(true);
    
    try {
      const response = await axios.post(`${API_URL}/auth/upload-avatar`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log('上传头像响应数据:', response.data);
      
      if (response.data.avatar_url) {
        // 设置本地状态
        setAvatarUrl(response.data.avatar_url);
        console.log('设置新的头像URL:', response.data.avatar_url);
        console.log('完整的头像URL:', `${STATIC_URL}${response.data.avatar_url}`);
        
        // 更新全局用户状态
        if (user) {
          // 方法1: 直接更新
          const updatedUser = {
            ...user,
            avatar_url: response.data.avatar_url
          };
          console.log('更新用户信息:', updatedUser);
          updateUser(updatedUser);
          
          // 方法2: 从后端获取最新信息
          // 这里也可以再次获取最新的用户信息以确保同步
          try {
            const { checkAuth } = useAuthStore.getState();
            await checkAuth();
            console.log('已刷新全局用户信息');
          } catch (e) {
            console.error('刷新用户信息失败:', e);
          }
        }
        
        message.success('头像上传成功');
        onSuccess(response, file);
      } else {
        console.error('响应中没有avatar_url字段', response.data);
        message.error('头像URL获取失败');
        onError(new Error('No avatar_url in response'));
      }
    } catch (error) {
      console.error('头像上传错误:', error);
      message.error('头像上传失败');
      onError(error);
    } finally {
      setUploading(false);
    }
  };

  const handlePreview = async (file: any) => {
    if (!file.url && !file.preview) {
      file.preview = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.readAsDataURL(file.originFileObj);
        reader.onload = () => resolve(reader.result);
      });
    }
    setPreviewImage(file.url || file.preview);
    setPreviewOpen(true);
  };

  if (!user && !profile) {
    return <Skeleton active />;
  }

  // 确保有用户数据用于显示
  const userData: UserData = profile || user || {};

  return (
    <div className="profile-container" style={{ 
      width: '100%',
      padding: '32px 0'
    }}>
      <div className="profile-header" style={{ marginBottom: '32px', textAlign: 'center' }}>
        <Title level={2} style={{ fontSize: '28px', marginBottom: '12px' }}>个人资料</Title>
        <Text type="secondary" style={{ fontSize: '16px' }}>管理您的账户信息和密码</Text>
      </div>

      <Row gutter={[32, 32]}>
        <Col xs={24} lg={6}>
          <Card 
            className="profile-card" 
            style={{ 
              borderRadius: '12px', 
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
              height: '100%',
              border: 'none'
            }}
          >
            <div className="profile-avatar" style={{ textAlign: 'center', padding: '32px 0' }}>
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <Avatar 
                  size={140} 
                  icon={<UserOutlined />} 
                  src={avatarUrl && `${STATIC_URL}${avatarUrl}`}
                  style={{ 
                    backgroundColor: '#1890ff',
                    fontSize: '60px',
                    boxShadow: '0 6px 16px rgba(0,0,0,0.15)'
                  }}
                />
                <div style={{ position: 'absolute', right: '0', bottom: '0' }}>
                  <Upload 
                    accept="image/*"
                    showUploadList={false}
                    customRequest={handleAvatarUpload}
                    onPreview={handlePreview}
                  >
                    <Button 
                      type="primary" 
                      shape="circle" 
                      icon={<CameraOutlined />} 
                      size="large"
                      loading={uploading}
                      style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}
                    />
                  </Upload>
                </div>
              </div>
              <div style={{ marginTop: 32 }}>
                <Title level={3} style={{ marginBottom: 12, fontSize: '24px' }}>{userData.username}</Title>
                <Text type="secondary" style={{ fontSize: '16px' }}>{userData.email}</Text>
              </div>
            </div>
            
            <Divider style={{ margin: '16px 0 24px' }} />
            
            <Space direction="vertical" size="large" style={{ width: '100%', padding: '0 16px' }}>
              {userData.created_at && (
                <div>
                  <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: '4px' }}>注册时间</Text>
                  <div style={{ fontSize: '16px' }}>{formatDate(userData.created_at)}</div>
                </div>
              )}
              {userData.updated_at && (
                <div>
                  <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: '4px' }}>最后更新</Text>
                  <div style={{ fontSize: '16px' }}>{formatDate(userData.updated_at)}</div>
                </div>
              )}
              {userData.is_active !== undefined && (
                <div>
                  <Text type="secondary" style={{ fontSize: '14px', display: 'block', marginBottom: '4px' }}>账户状态</Text>
                  <div style={{ fontSize: '16px' }}>{userData.is_active ? '已激活' : '未激活'}</div>
                </div>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={18}>
          <Space direction="vertical" size="large" style={{ width: '100%', display: 'flex' }}>
            <Card 
              className="profile-card" 
              title={<span style={{ fontSize: '20px', fontWeight: 'bold' }}>基本信息</span>}
              style={{ 
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                border: 'none'
              }}
              styles={{
                header: { borderBottom: '1px solid #f0f0f0', padding: '16px 24px' },
                body: { padding: '24px' }
              }}
            >
              <Form 
                layout="vertical" 
                initialValues={userData}
                onFinish={handleUpdateProfile}
                size="large"
                style={{ width: '100%' }}
              >
                <Form.Item 
                  label="用户名" 
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input prefix={<UserOutlined />} placeholder="用户名" style={{ height: '48px' }} />
                </Form.Item>

                <Form.Item 
                  label="邮箱" 
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '请输入有效的邮箱' }
                  ]}
                >
                  <Input prefix={<MailOutlined />} placeholder="邮箱" style={{ height: '48px' }} />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    style={{ height: '48px', fontSize: '16px', width: '140px' }}
                  >
                    保存修改
                  </Button>
                </Form.Item>
              </Form>
            </Card>

            <Card 
              className="profile-card" 
              title={<span style={{ fontSize: '20px', fontWeight: 'bold' }}>修改密码</span>}
              style={{ 
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                border: 'none'
              }}
              styles={{
                header: { borderBottom: '1px solid #f0f0f0', padding: '16px 24px' },
                body: { padding: '24px' }
              }}
            >
              <Form 
                form={passwordForm}
                layout="vertical" 
                onFinish={handleChangePassword}
                size="large"
                style={{ width: '100%' }}
              >
                <Form.Item 
                  label="当前密码" 
                  name="current_password"
                  rules={[{ required: true, message: '请输入当前密码' }]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="当前密码" style={{ height: '48px' }} />
                </Form.Item>

                <Form.Item 
                  label="新密码" 
                  name="new_password"
                  rules={[
                    { required: true, message: '请输入新密码' },
                    { min: 6, message: '密码长度不能少于6个字符' }
                  ]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="新密码" style={{ height: '48px' }} />
                </Form.Item>

                <Form.Item 
                  label="确认新密码" 
                  name="confirm_password"
                  rules={[
                    { required: true, message: '请确认新密码' },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('new_password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error('两次输入的密码不一致'));
                      },
                    }),
                  ]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" style={{ height: '48px' }} />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    style={{ height: '48px', fontSize: '16px', width: '140px' }}
                  >
                    更新密码
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </Space>
        </Col>
      </Row>

      <Modal
        open={previewOpen}
        title="预览头像"
        footer={null}
        onCancel={() => setPreviewOpen(false)}
        width={520}
        style={{ top: '20%' }}
      >
        <img alt="预览" style={{ width: '100%' }} src={previewImage} />
      </Modal>
    </div>
  );
};

export default Profile;