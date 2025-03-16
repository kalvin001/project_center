import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { Button, Dropdown, Space, Avatar, notification } from 'antd';
import type { MenuProps } from 'antd';
import { ProLayout } from '@ant-design/pro-layout';
import {
  DashboardOutlined,
  ProjectOutlined,
  PlusCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  CloudServerOutlined,
  AppstoreOutlined,
  UserSwitchOutlined,
  DeploymentUnitOutlined,
  FileTextOutlined,
  BugOutlined
} from '@ant-design/icons';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import ProjectCreate from './pages/ProjectCreate';
import MachineManagement from './pages/MachineManagement';
import MachineDetail from './pages/MachineDetail';
import MachineEdit from './pages/MachineEdit';
import Profile from './pages/Profile';
import Deployment from './pages/Deployment';
import DeploymentDetail from './pages/DeploymentDetail';
import LogsPage from './pages/LogsPage';
import ApiTester from './components/debug/ApiTester';
import { useAuthStore } from './stores/authStore';
import { API_URL, STATIC_URL } from './utils/constants';

// 定义路由项的类型
interface MenuItem {
  path: string;
  name: string;
  icon?: React.ReactNode;
}

// 主布局组件
const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  // 组件挂载时获取最新用户信息
  React.useEffect(() => {
    // 获取最新的用户信息，包括头像URL
    checkAuth();
  }, []);

  // 添加一个useEffect检查头像URL
  React.useEffect(() => {
    if (user?.avatar_url) {
      console.log('App中的头像URL:', user.avatar_url);
      console.log('拼接后的完整URL:', `${STATIC_URL}${user.avatar_url}`);
      
      // 测试图片是否可访问
      const img = new Image();
      img.onload = () => console.log('头像图片加载成功');
      img.onerror = () => console.error('头像图片加载失败');
      img.src = `${STATIC_URL}${user.avatar_url}`;
    } else {
      console.log('用户数据中没有头像URL');
    }
  }, [user]);

  const handleLogout = () => {
    logout();
  };

  // 定义下拉菜单项
  const userMenuItems: MenuProps['items'] = [
    {
      key: '1',
      icon: <UserSwitchOutlined />,
      label: '个人资料',
      onClick: () => {
        navigate('/profile');
      }
    },
    {
      key: '2',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout
    }
  ];

  // 定义菜单项
  const menuItems = [
    {
      path: '/',
      name: '首页',
      icon: <DashboardOutlined />
    },
    {
      path: '/projects',
      name: '项目',
      icon: <ProjectOutlined />
    }, 
    {
      path: '/machines',
      name: '机器',
      icon: <CloudServerOutlined />
    },
    {
      path: '/deployment',
      name: '部署',
      icon: <DeploymentUnitOutlined />
    },
    {
      name: '监控',
      icon: <FileTextOutlined />,
      children: [
        {
          path: '/logs',
          name: '系统日志',
          icon: <FileTextOutlined />
        },
        {
          name: '调试工具',
          icon: <BugOutlined />,
          path: '/debug',
          access: 'admin'
        }
      ]
    }
  ];

  return (
    <ProLayout
      title="项目中心"
      //layout="side"Hey, Cortana. Hey, Cortana. Hey, Cortana. 
      layout="top"

      logo={<AppstoreOutlined />} 
      navTheme="light"
      headerTheme="light" 
      contentWidth="Fluid"
      collapsed={collapsed}
      onCollapse={setCollapsed}
      // avatarProps={{
      //   src: 'https://gw.alipayobjects.com/zos/antfincdn/efFD%24IOql2/weixintupian_20170331104822.jpg',
      //   size: 'small',
      //   title: '七妮妮',
      // }}

      actionsRender={() => ( 
          <Dropdown menu={{ items: userMenuItems }} >
            <span style={{ cursor: 'pointer', marginRight: '16px' }}>
              <Space>
                <Avatar 
                  icon={<UserOutlined />} 
                  src={user?.avatar_url ? `${STATIC_URL}${user.avatar_url}` : undefined}
                  style={{ marginRight: 8 }} 
                />
                {user?.username || ''}
              </Space>
            </span>
          </Dropdown> 
      )}
      menu={{ 
        type: 'group',
        defaultOpenAll: true 
      }}
      menuItemRender={(item: MenuItem, dom: React.ReactNode) => (
        <Link to={item.path || '/'} onClick={() => navigate(item.path || '/')}>
          {dom}
        </Link>
      )}
      route={{ 
        path: '/', 
        routes: menuItems 
      }}
      waterMarkProps={{
        content: user?.username || '',
      }}
    >
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail key={window.location.pathname} />} />
        <Route path="/create-project" element={<ProjectCreate />} />
        <Route path="/machines" element={<MachineManagement />} />
        <Route path="/machines/:id" element={<MachineDetail />} />
        <Route path="/machines/add" element={<MachineEdit />} />
        <Route path="/machines/edit/:id" element={<MachineEdit />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/deployment" element={<Deployment />} />
        <Route path="/deployments/:id" element={<DeploymentDetail />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/debug" element={<ApiTester />} />
      </Routes>
    </ProLayout>
  );
};

function App() {
  const { token } = useAuthStore();

  return (
    <Router>
      {!token ? (
        <Login />
      ) : (
        <MainLayout />
      )}
    </Router>
  );
}

export default App; 