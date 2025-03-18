import React from 'react';
import { Card, Typography, Row, Col, Button } from 'antd';
import { 
  ScanOutlined, 
  HistoryOutlined, 
  SettingOutlined 
} from '@ant-design/icons';
import { Link } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  return (
    <div className="home-page">
      <div className="page-header" style={{ textAlign: 'center', margin: '24px 0 48px' }}>
        <Title level={1}>Handwritten Label AI Assistant</Title>
        <Paragraph style={{ fontSize: '16px' }}>
          Extract text and structured data from handwritten labels using advanced AI
        </Paragraph>
      </div>
      
      <Row gutter={[24, 24]} justify="center">
        <Col xs={24} sm={12} md={8}>
          <Card hoverable>
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <ScanOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              <Title level={3}>Recognition</Title>
              <Paragraph>
                Upload images of handwritten labels to extract text and structured data
              </Paragraph>
              <Link to="/recognition">
                <Button type="primary" size="large" icon={<ScanOutlined />}>
                  Start Recognition
                </Button>
              </Link>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card hoverable>
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <HistoryOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
              <Title level={3}>History</Title>
              <Paragraph>
                View and manage your previous recognition results
              </Paragraph>
              <Link to="/history">
                <Button size="large" icon={<HistoryOutlined />}>
                  View History
                </Button>
              </Link>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card hoverable>
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <SettingOutlined style={{ fontSize: '48px', color: '#722ed1' }} />
              <Title level={3}>Settings</Title>
              <Paragraph>
                Configure models, API keys, and application preferences
              </Paragraph>
              <Link to="/settings">
                <Button size="large" icon={<SettingOutlined />}>
                  Go to Settings
                </Button>
              </Link>
            </div>
          </Card>
        </Col>
      </Row>
      
      <Card style={{ marginTop: 48 }}>
        <Title level={3}>How It Works</Title>
        <Row gutter={[24, 24]}>
          <Col span={8}>
            <div className="step">
              <div className="step-number">1</div>
              <Title level={4}>Upload</Title>
              <Paragraph>
                Upload an image containing handwritten text. You can use the drag and drop interface or select a file.
              </Paragraph>
            </div>
          </Col>
          
          <Col span={8}>
            <div className="step">
              <div className="step-number">2</div>
              <Title level={4}>Process</Title>
              <Paragraph>
                The image is processed by advanced AI models, which extract text and identify structured data.
              </Paragraph>
            </div>
          </Col>
          
          <Col span={8}>
            <div className="step">
              <div className="step-number">3</div>
              <Title level={4}>Review</Title>
              <Paragraph>
                Review and edit the extracted information if needed, then use it in your workflow.
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default HomePage;
