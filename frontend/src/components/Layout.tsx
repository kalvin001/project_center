import React from 'react'
import { Layout as AntLayout, Menu, Button, Dropdown, Space, theme } from 'antd'
import { Outlet, useNavigate, useLocation, useParams } from 'react-router-dom'
import {
  DashboardOutlined,
  ProjectOutlined,
  PlusOutlined,
  UserOutlined,
  LogoutOutlined,
  DownOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../stores/authStore'

const { Header, Content, Sider } = AntLayout

const Layout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { token } = theme.useToken()
  const params = useParams()
  const isProfilePage = location.pathname === '/profile'
  
  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname
    if (path === '/') return ['dashboard']
    if (path.startsWith('/projects') && !path.includes('/create')) return ['projects']
    if (path.includes('/create')) return ['create-project']
    if (path.includes('/profile')) return ['profile']
    return []
  }
  
  // 用户菜单项
  const userMenuItems = [
    {
      key: 'profile',
      label: '个人资料',
      icon: <UserOutlined />,
      onClick: () => navigate('/profile'),
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]
  
  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header className="header" style={{ padding: '0 20px', background: token.colorBgContainer }}>
        <div className="logo" style={{ color: token.colorText }}>
          <img src="/logo.svg" alt="项目管理中心" style={{ height: '28px', marginRight: '10px' }} />
          项目管理中心
        </div>
        <div className="header-right">
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" style={{ color: token.colorText }}>
              <Space>
                <UserOutlined />
                {user?.username || '用户'}
                <DownOutlined />
              </Space>
            </Button>
          </Dropdown>
        </div>
      </Header>
      <AntLayout>
        {/* {!isProfilePage && (
          <Sider width={200} style={{ background: token.colorBgContainer }}>
            <Menu
              mode="inline"
              selectedKeys={getSelectedKey()}
              style={{ height: '100%', borderRight: 0 }}
              items={[
                {
                  key: 'dashboard',
                  icon: <DashboardOutlined />,
                  label: '仪表盘',
                  onClick: () => navigate('/'),
                },
                {
                  key: 'projects',
                  icon: <ProjectOutlined />,
                  label: '项目列表',
                  onClick: () => navigate('/projects'),
                },
                {
                  key: 'create-project',
                  icon: <PlusOutlined />,
                  label: '创建项目',
                  onClick: () => navigate('/create-project'),
                },
              ]}
            />
          </Sider>
        )} */}
        <AntLayout style={{ padding: '0' }}>
          <Content
            className="site-layout-content"
            style={{
              padding: isProfilePage ? 0 : 24,
              margin: isProfilePage ? 0 : '16px 0',
              minHeight: 280,
              background: isProfilePage ? 'transparent' : token.colorBgContainer,
              maxWidth: '100%'
            }}
          >
            <Outlet />
          </Content>
        </AntLayout>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout 