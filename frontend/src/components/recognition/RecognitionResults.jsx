import React from 'react';
import { 
  Card, 
  Typography, 
  Descriptions, 
  Divider,
  Tag,
  Button,
  Row,
  Col,
  Image
} from 'antd';
import { 
  EditOutlined, 
  CheckCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import ConfidenceIndicator from '../common/ConfidenceIndicator';

const { Title, Text, Paragraph } = Typography;

const RecognitionResults = ({ 
  result, 
  originalImage,
  onRequestReview 
}) => {
  if (!result) return null;
  
  const recognitionData = result.recognition?.recognition || {};
  const qualityData = result.recognition?.quality || {};
  const finalResult = result.final_result || {};
  const nextStep = result.next_step;
  
  const showReviewButton = nextStep === 'human_review';
  const extractedText = finalResult.text || '';
  const structuredData = finalResult.structured_data || {};
  const confidence = finalResult.confidence || 0;
  
  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FileTextOutlined style={{ marginRight: 8 }} />
          <span>Recognition Results</span>
          {result.models_used?.recognition && (
            <Tag color="blue" style={{ marginLeft: 12 }}>
              Model: {result.models_used.recognition}
            </Tag>
          )}
        </div>
      }
      extra={
        showReviewButton ? (
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={onRequestReview}
          >
            Review & Edit
          </Button>
        ) : (
          <Tag 
            color="success" 
            icon={<CheckCircleOutlined />}
          >
            Processed
          </Tag>
        )
      }
    >
      <Row gutter={24}>
        {originalImage && (
          <Col span={8}>
            <div style={{ marginBottom: 16 }}>
              <Title level={5}>Original Image</Title>
              <Image 
                src={originalImage} 
                alt="Original image"
                style={{ maxWidth: '100%' }}
              />
            </div>
          </Col>
        )}
        
        <Col span={originalImage ? 16 : 24}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Title level={5}>Extracted Text</Title>
              <ConfidenceIndicator value={confidence} />
            </div>
            <Card style={{ background: '#f5f5f5' }}>
              <Paragraph 
                copyable={{ text: extractedText }}
                style={{ whiteSpace: 'pre-wrap' }}
              >
                {extractedText || 'No text extracted'}
              </Paragraph>
            </Card>
          </div>
          
          <Divider />
          
          <div>
            <Title level={5}>Structured Data</Title>
            {Object.keys(structuredData).length > 0 ? (
              <Descriptions
                bordered
                size="small"
                column={1}
              >
                {Object.entries(structuredData).map(([key, value]) => (
                  <Descriptions.Item 
                    key={key} 
                    label={key}
                    labelStyle={{ fontWeight: 'bold' }}
                  >
                    {value}
                  </Descriptions.Item>
                ))}
              </Descriptions>
            ) : (
              <Text type="secondary">No structured data extracted</Text>
            )}
          </div>
          
          {qualityData.issues && qualityData.issues.length > 0 && (
            <>
              <Divider />
              <div>
                <Title level={5}>Recognition Issues</Title>
                <ul>
                  {qualityData.issues.map((issue, index) => (
                    <li key={index}>
                      <Text type="warning">{issue}</Text>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </Col>
      </Row>
    </Card>
  );
};

export default RecognitionResults;
