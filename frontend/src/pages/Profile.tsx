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
  Skeleton
} from 'antd';
import { UserOutlined, MailOutlined, LockOutlined, UploadOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import axios from 'axios';

const { Title, Text } = Typography;
const API_URL = 'http://localhost:8011/api';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  created_at: string;
  last_login: string;
  projects_count: number;
}

const Profile: React.FC = () => {
  const { user, token, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [passwordForm] = Form.useForm();

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
    } catch (error) {
      message.error('获取个人资料失败');
      console.error(error);
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
      console.error(error);
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
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <Skeleton active />;
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <Title level={2}>个人资料</Title>
        <Text type="secondary">管理您的账户信息和密码</Text>
      </div>

      <Row gutter={24}>
        <Col xs={24} md={8}>
          <Card className="profile-card">
            <div className="profile-avatar" style={{ textAlign: 'center' }}>
              <Avatar 
                size={100} 
                icon={<UserOutlined />} 
                style={{ backgroundColor: '#1890ff' }}
              />
              <div style={{ marginTop: 16 }}>
                <Upload 
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={() => false}
                >
                  <Button icon={<UploadOutlined />}>更新头像</Button>
                </Upload>
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <Title level={4}>{user.username}</Title>
              <Text type="secondary">{user.email}</Text>
            </div>
            {profile && (
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">注册时间: {new Date(profile.created_at).toLocaleString()}</Text>
                <br />
                <Text type="secondary">上次登录: {new Date(profile.last_login).toLocaleString()}</Text>
                <br />
                <Text type="secondary">项目数量: {profile.projects_count || 0}</Text>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} md={16}>
          <Card className="profile-card" title="基本信息">
            <Form 
              layout="vertical" 
              initialValues={user} 
              onFinish={handleUpdateProfile}
            >
              <Form.Item 
                label="用户名" 
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="用户名" />
              </Form.Item>

              <Form.Item 
                label="邮箱" 
                name="email"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱' }
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="邮箱" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  保存修改
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Card className="profile-card" title="修改密码">
            <Form 
              form={passwordForm}
              layout="vertical" 
              onFinish={handleChangePassword}
            >
              <Form.Item 
                label="当前密码" 
                name="current_password"
                rules={[{ required: true, message: '请输入当前密码' }]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="当前密码" />
              </Form.Item>

              <Form.Item 
                label="新密码" 
                name="new_password"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 6, message: '密码长度不能少于6个字符' }
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="新密码" />
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
                <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  更新密码
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Profile; 