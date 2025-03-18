import React, { useState } from 'react';
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  List,
  Tag,
  Alert,
  Divider,
  Space
} from 'antd';
import {
  EditOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { toast } from 'react-toastify';
import { submitHumanReview } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ReviewInterface = ({ 
  workflowResult, 
  workflowId,
  onReviewComplete 
}) => {
  const [form] = Form.useForm();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Extract data from the workflow result
  const finalResult = workflowResult?.final_result || {};
  const reviewData = workflowResult?.review || {};
  const originalText = finalResult.text || '';
  const originalStructuredData = finalResult.structured_data || {};
  const suggestions = reviewData?.review?.suggestions || [];
  
  // Initialize form with current values
  React.useEffect(() => {
    form.setFieldsValue({
      corrected_text: originalText,
      comments: ''
    });
    
    // Initialize structured data fields
    Object.entries(originalStructuredData).forEach(([key, value]) => {
      form.setFieldsValue({
        [`structured_data_${key}`]: value
      });
    });
  }, [form, originalText, originalStructuredData]);
  
  const handleSubmit = async (values) => {
    try {
      setIsSubmitting(true);
      
      // Reconstruct structured data from form fields
      const structuredData = {};
      Object.keys(values).forEach(key => {
        if (key.startsWith('structured_data_')) {
          const fieldName = key.replace('structured_data_', '');
          structuredData[fieldName] = values[key];
        }
      });
      
      // Convert structured data to JSON string for submission
      const structuredDataString = JSON.stringify(structuredData);
      
      const formData = new FormData();
      formData.append('workflow_id', workflowId);
      formData.append('corrected_text', values.corrected_text);
      formData.append('corrected_structured_data', structuredDataString);
      formData.append('comments', values.comments);
      
      const result = await submitHumanReview(formData);
      
      toast.success('Human review submitted successfully');
      onReviewComplete?.(result);
    } catch (error) {
      console.error('Error submitting review:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <EditOutlined style={{ marginRight: 8 }} />
          <span>Human Review</span>
        </div>
      }
    >
      {suggestions.length > 0 && (
        <Alert
          message="Review Suggestions"
          description={
            <List
              size="small"
              dataSource={suggestions}
              renderItem={suggestion => (
                <List.Item>
                  <InfoCircleOutlined style={{ marginRight: 8 }} />
                  {suggestion}
                </List.Item>
              )}
            />
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="corrected_text"
          label="Extracted Text"
          rules={[{ required: true, message: 'Please enter the corrected text' }]}
        >
          <TextArea
            rows={6}
            placeholder="Edit the recognized text here"
          />
        </Form.Item>
        
        <Divider>Structured Data</Divider>
        
        {Object.entries(originalStructuredData).map(([key, value]) => (
          <Form.Item
            key={key}
            name={`structured_data_${key}`}
            label={key}
          >
            <Input placeholder={`Enter ${key}`} />
          </Form.Item>
        ))}
        
        <Form.Item
          name="comments"
          label="Comments"
        >
          <TextArea
            rows={3}
            placeholder="Add any comments about your corrections"
          />
        </Form.Item>
        
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Space>
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              htmlType="submit"
              loading={isSubmitting}
            >
              Submit Corrections
            </Button>
            <Button
              icon={<CloseCircleOutlined />}
              onClick={() => onReviewComplete?.(workflowResult)}
            >
              Cancel
            </Button>
          </Space>
        </div>
      </Form>
    </Card>
  );
};

export default ReviewInterface;
