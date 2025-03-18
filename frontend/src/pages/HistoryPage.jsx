// src/pages/HistoryPage.jsx
import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Typography, 
  Button, 
  Tag, 
  Empty,
  Space,
  Modal,
  Image 
} from 'antd';
import { 
  EyeOutlined, 
  DeleteOutlined, 
  ExclamationCircleOutlined 
} from '@ant-design/icons';
import RecognitionResults from '../components/recognition/RecognitionResults';
import ConfidenceIndicator from '../components/common/ConfidenceIndicator';

const { Title, Text } = Typography;
const { confirm } = Modal;

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  
  // Load history from localStorage
  useEffect(() => {
    const loadHistory = () => {
      try {
        const savedHistory = localStorage.getItem('recognition_history');
        if (savedHistory) {
          const parsedHistory = JSON.parse(savedHistory);
          console.log('Loaded history:', parsedHistory); // Add this for debugging
          setHistory(parsedHistory);
        } else {
          console.log('No history found in localStorage'); // Add this for debugging
        }
      } catch (err) {
        console.error('Error loading history:', err);
      }
    };
    
    loadHistory();
  }, []);
  
  const handleViewResult = (record) => {
    setSelectedResult(record);
    setIsModalVisible(true);
  };
  
  const handleDeleteResult = (record) => {
    confirm({
      title: 'Are you sure you want to delete this result?',
      icon: <ExclamationCircleOutlined />,
      content: 'This action cannot be undone.',
      onOk() {
        const updatedHistory = history.filter(item => item.id !== record.id);
        setHistory(updatedHistory);
        localStorage.setItem('recognition_history', JSON.stringify(updatedHistory));
      }
    });
  };
  
  const handleModalClose = () => {
    setIsModalVisible(false);
  };
  
  const columns = [
    {
      title: 'Date',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: timestamp => new Date(timestamp * 1000).toLocaleString()
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      render: confidence => <ConfidenceIndicator value={confidence} />
    },
    {
      title: 'Model',
      dataIndex: 'model',
      key: 'model',
      render: model => <Tag color="blue">{model}</Tag>
    },
    {
      title: 'Status',
      dataIndex: 'next_step',
      key: 'next_step',
      render: status => {
        let color;
        let text;
        
        switch (status) {
          case 'approve':
            color = 'success';
            text = 'Approved';
            break;
          case 'human_review':
            color = 'warning';
            text = 'Needs Review';
            break;
          case 'complete':
            color = 'success';
            text = 'Completed';
            break;
          default:
            color = 'default';
            text = 'Unknown';
        }
        
        return <Tag color={color}>{text}</Tag>;
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="primary" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewResult(record)}
          >
            View
          </Button>
          <Button 
            type="default" 
            danger 
            size="small" 
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteResult(record)}
          >
            Delete
          </Button>
        </Space>
      )
    }
  ];
  
  return (
    <div className="history-page">
      <Title level={2}>Recognition History</Title>
      
      <Card>
        {history.length > 0 ? (
          <Table 
            dataSource={history} 
            columns={columns} 
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        ) : (
          <Empty 
            description="No recognition history found" 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
      
      <Modal
        title="Recognition Result"
        open={isModalVisible}
        onCancel={handleModalClose}
        footer={[
          <Button key="close" onClick={handleModalClose}>
            Close
          </Button>
        ]}
        width={900}
      >
        {selectedResult && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Date: </Text>
              <Text>{new Date(selectedResult.timestamp * 1000).toLocaleString()}</Text>
            </div>
            
            {selectedResult.image_url && (
              <div style={{ marginBottom: 16 }}>
                <Title level={5}>Original Image</Title>
                <Image 
                  src={selectedResult.image_url}
                  alt="Original image"
                  style={{ maxWidth: '100%' }}
                />
              </div>
            )}
            
            <RecognitionResults result={selectedResult} />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HistoryPage;
