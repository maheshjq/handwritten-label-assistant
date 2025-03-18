// src/pages/SettingsPage.jsx
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Select, 
  Divider, 
  Alert,
  Typography,
  Tabs 
} from 'antd';
import { 
  CloudOutlined, 
  LockOutlined, 
  DatabaseOutlined,
  SaveOutlined
} from '@ant-design/icons';
import { toast } from 'react-toastify';
import { testModel } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const SettingsPage = () => {
  const [form] = Form.useForm();
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  
  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('app_settings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        form.setFieldsValue(settings);
      } catch (err) {
        console.error('Error loading settings:', err);
      }
    }
  }, [form]);
  
  const handleSaveSettings = (values) => {
    try {
      localStorage.setItem('app_settings', JSON.stringify(values));
      toast.success('Settings saved successfully');
    } catch (err) {
      console.error('Error saving settings:', err);
      toast.error('Failed to save settings');
    }
  };
  
  const handleTestConnection = async () => {
    try {
      setTestLoading(true);
      setTestResult(null);
      
      const modelName = form.getFieldValue('default_model');
      const result = await testModel(modelName, 'Test message from the Handwritten Label AI Assistant');
      
      setTestResult({
        success: true,
        output: result.output,
        model: result.model,
        provider: result.provider
      });
      
      toast.success('Connection test successful!');
    } catch (error) {
      console.error('Test connection error:', error);
      
      setTestResult({
        success: false,
        error: error.response?.data?.detail || error.message
      });
      
      toast.error('Connection test failed');
    } finally {
      setTestLoading(false);
    }
  };
  
  return (
    <div className="settings-page">
      <Title level={2}>Settings</Title>
      
      <Card>
        <Tabs defaultActiveKey="api">
          <TabPane 
            tab={
              <span>
                <CloudOutlined /> API Connections
              </span>
            } 
            key="api"
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSaveSettings}
            >
              <Title level={4}>Provider API Keys</Title>
              <Paragraph type="secondary">
                Add API keys to connect to external LLM providers
              </Paragraph>
              
              <Form.Item
                name="groq_api_key"
                label="Groq API Key"
                rules={[{ required: false }]}
              >
                <Input.Password 
                  placeholder="Enter Groq API key" 
                  prefix={<LockOutlined />}
                />
              </Form.Item>
              
              <Form.Item
                name="claude_api_key"
                label="Claude API Key"
                rules={[{ required: false }]}
              >
                <Input.Password 
                  placeholder="Enter Claude API key" 
                  prefix={<LockOutlined />}
                />
              </Form.Item>
              
              <Form.Item
                name="openai_api_key"
                label="OpenAI API Key"
                rules={[{ required: false }]}
              >
                <Input.Password 
                  placeholder="Enter OpenAI API key" 
                  prefix={<LockOutlined />}
                />
              </Form.Item>
              
              <Divider />
              
              <Title level={4}>API Server Settings</Title>
              
              <Form.Item
                name="api_url"
                label="API Server URL"
                initialValue="http://localhost:8000/api"
                rules={[{ required: true }]}
              >
                <Input placeholder="Enter API server URL" />
              </Form.Item>
              
              <Form.Item
                name="default_model"
                label="Default Recognition Model"
                initialValue="llava:latest"
              >
                <Select placeholder="Select default model">
                  <Option value="llava:latest">LLaVA (Latest)</Option>
                  <Option value="bakllava:latest">BakLLaVA (Latest)</Option>
                  <Option value="llava:13b">LLaVA 13B</Option>
                  <Option value="llava:7b">LLaVA 7B</Option>
                </Select>
              </Form.Item>
              
              <Button 
                type="default" 
                onClick={handleTestConnection}
                loading={testLoading}
              >
                Test Connection
              </Button>
              
              {testResult && (
                <div style={{ marginTop: 16 }}>
                  <Alert
                    message={testResult.success ? "Connection Successful" : "Connection Failed"}
                    description={
                      testResult.success ? (
                        <div>
                          <p><strong>Model:</strong> {testResult.model}</p>
                          <p><strong>Provider:</strong> {testResult.provider}</p>
                          <p><strong>Response:</strong> {testResult.output}</p>
                        </div>
                      ) : (
                        <p>Error: {testResult.error}</p>
                      )
                    }
                    type={testResult.success ? "success" : "error"}
                    showIcon
                  />
                </div>
              )}
              
              <Divider />
              
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<SaveOutlined />}
              >
                Save Settings
              </Button>
            </Form>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <DatabaseOutlined /> Storage Settings
              </span>
            } 
            key="storage"
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSaveSettings}
            >
              <Title level={4}>Storage Options</Title>
              
              <Form.Item
                name="enable_cache"
                label="Enable Caching"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch />
              </Form.Item>
              <Text type="secondary">
                Cache recognition results to improve performance
              </Text>
              
              <Form.Item
                name="enable_storage"
                label="Enable Storage"
                valuePropName="checked"
                initialValue={true}
                style={{ marginTop: 24 }}
              >
                <Switch />
              </Form.Item>
              <Text type="secondary">
                Store uploaded images and recognition results
              </Text>
              
              <Form.Item
                name="storage_retention_days"
                label="Storage Retention (days)"
                initialValue={30}
                style={{ marginTop: 24 }}
              >
                <Select>
                  <Option value={1}>1 day</Option>
                  <Option value={7}>7 days</Option>
                  <Option value={30}>30 days</Option>
                  <Option value={90}>90 days</Option>
                  <Option value={365}>365 days</Option>
                </Select>
              </Form.Item>
              
              <Divider />
              
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<SaveOutlined />}
              >
                Save Settings
              </Button>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SettingsPage;
