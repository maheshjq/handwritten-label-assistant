import React, { useEffect, useState } from 'react';
import { Select, Spin, Typography, Tag } from 'antd';
import { fetchAvailableModels } from '../../services/api';

const { Option } = Select;
const { Text } = Typography;

// Map provider to tag color
const providerColors = {
  ollama: 'blue',
  groq: 'purple',
  claude: 'green',
  openai: 'red'
};

const ModelSelector = ({ onChange, value, disabled }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadModels = async () => {
      try {
        setLoading(true);
        const modelData = await fetchAvailableModels();
        setModels(modelData.models);
        
        // Set default model if no value is provided
        if (!value && modelData.default_model) {
          onChange?.(modelData.default_model);
        }
      } catch (err) {
        console.error('Failed to load models:', err);
        setError('Failed to load available models');
      } finally {
        setLoading(false);
      }
    };
    
    loadModels();
  }, [onChange, value]);
  
  if (loading) {
    return <Spin size="small" />;
  }
  
  if (error) {
    return <Text type="danger">{error}</Text>;
  }
  
  return (
    <Select 
      style={{ width: '100%' }}
      placeholder="Select a model"
      onChange={onChange}
      value={value}
      disabled={disabled}
    >
      {models.map(model => (
        <Option key={model.name} value={model.name}>
          {model.name}
          <Tag color={providerColors[model.provider]} style={{ marginLeft: 8 }}>
            {model.provider}
          </Tag>
        </Option>
      ))}
    </Select>
  );
};

export default ModelSelector;
