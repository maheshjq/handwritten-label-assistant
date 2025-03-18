import React, { useState } from 'react';
import { 
  Card, 
  Button, 
  Form, 
  Switch, 
  Space, 
  Typography,
  Divider
} from 'antd';
import { 
  ScanOutlined,
  SettingOutlined 
} from '@ant-design/icons';
import ImageUploader from '../common/ImageUploader';
import ModelSelector from '../common/ModelSelector';
import { recognizeHandwriting } from '../../services/api';
import { toast } from 'react-toastify';

const { Title, Text } = Typography;

const RecognitionForm = ({ onRecognitionComplete, onProcessingStart }) => {
  const [form] = Form.useForm();
  const [imageFile, setImageFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const handleImageUpload = (file) => {
    setImageFile(file);
  };
  
  const handleSubmit = async (values) => {
    if (!imageFile) {
      toast.error('Please upload an image first');
      return;
    }
    
    try {
      setIsLoading(true);
      onProcessingStart?.();
      
      const formData = new FormData();
      formData.append('file', imageFile);
      
      if (values.model_name) {
        formData.append('model_name', values.model_name);
      }
      
      formData.append('preprocess', values.preprocess);
      formData.append('skip_review', values.skip_review);
      
      const result = await recognizeHandwriting(formData);
      onRecognitionComplete?.(result);
      toast.success('Recognition completed successfully');
    } catch (error) {
      console.error('Recognition error:', error);
      toast.error(error.response?.data?.detail || 'Recognition failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card title="Handwritten Label Recognition">
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          model_name: undefined,
          preprocess: true,
          skip_review: false
        }}
        onFinish={handleSubmit}
      >
        <ImageUploader 
          onImageUpload={handleImageUpload} 
          isLoading={isLoading}
        />
        
        <div style={{ marginTop: 16 }}>
          <Form.Item name="model_name" label="Recognition Model">
            <ModelSelector disabled={isLoading} />
          </Form.Item>
          
          <Button 
            type="link" 
            icon={<SettingOutlined />}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </Button>
          
          {showAdvanced && (
            <div className="advanced-options">
              <Divider />
              <Form.Item 
                name="preprocess" 
                valuePropName="checked"
                label="Preprocess Image"
              >
                <Switch disabled={isLoading} />
              </Form.Item>
              <Text type="secondary">
                Enhance image quality before processing (recommended)
              </Text>
              
              <Form.Item 
                name="skip_review" 
                valuePropName="checked"
                label="Skip Review Step"
                style={{ marginTop: 16 }}
              >
                <Switch disabled={isLoading} />
              </Form.Item>
              <Text type="secondary">
                Skip the AI review step (faster but less accurate)
              </Text>
            </div>
          )}
        </div>
        
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Button 
            type="primary" 
            icon={<ScanOutlined />}
            htmlType="submit"
            loading={isLoading}
            disabled={!imageFile}
            size="large"
          >
            Process Image
          </Button>
        </div>
      </Form>
    </Card>
  );
};

export default RecognitionForm;
