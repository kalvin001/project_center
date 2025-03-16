import React from 'react';
import { Avatar } from 'antd';
import { UserOutlined } from '@ant-design/icons';

const API_URL = process.env.REACT_APP_API_URL;

const Header: React.FC = () => {
  const user = { avatar_url: '/path/to/avatar.jpg' }; // Replace with actual user data

  return (
    <div>
      <Avatar 
        icon={<UserOutlined />} 
        src={user?.avatar_url ? `${API_URL}${user.avatar_url}` : undefined} 
        style={{ marginRight: 8 }} 
      />
    </div>
  );
};

export default Header; 