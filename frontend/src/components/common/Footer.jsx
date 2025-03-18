import React from 'react';
import { Layout, Typography } from 'antd';

const { Footer } = Layout;
const { Text } = Typography;

const AppFooter = () => {
  return (
    <Footer style={{ textAlign: 'center' }}>
      <Text type="secondary">
        Handwritten Label AI Assistant ©{new Date().getFullYear()} - All processing done locally for privacy
      </Text>
    </Footer>
  );
};

export default AppFooter;
