import React from 'react';
import { Layout, Typography, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeOutlined, 
  ScanOutlined, 
  HistoryOutlined, 
  SettingOutlined 
} from '@ant-design/icons';

const { Header } = Layout;
const { Title } = Typography;

const AppHeader = () => {
  const location = useLocation();
  
  const menuItems = [
    { key: '/', label: 'Home', icon: <HomeOutlined /> },
    { key: '/recognition', label: 'Recognition', icon: <ScanOutlined /> },
    { key: '/history', label: 'History', icon: <HistoryOutlined /> },
    { key: '/settings', label: 'Settings', icon: <SettingOutlined /> }
  ];
  
  return (
    <Header className="app-header">
      <div className="logo">
        <Title level={3} style={{ color: 'white', margin: 0 }}>
          Handwritten Label AI
        </Title>
      </div>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={menuItems.map(item => ({
          key: item.key,
          icon: item.icon,
          label: <Link to={item.key}>{item.label}</Link>
        }))}
      />
    </Header>
  );
};

export default AppHeader;
